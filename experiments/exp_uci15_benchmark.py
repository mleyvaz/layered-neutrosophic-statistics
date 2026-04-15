"""
UCI Benchmark — 15 datasets × 5 classifiers × 5 baselines
=========================================================

Reproduces Paper B (Neutrosophic Zone-Selective Classification) Table 3.

For each (dataset, classifier) pair we compute, under 5-fold stratified CV:
  - Classical     : argmax predict on raw classifier probabilities
  - Platt         : sigmoid calibration on held-out calibration split
  - Conformal     : split conformal, alpha=0.10, deferred when |prediction set| > 1
  - IS (interval) : [P - 0.15, P + 0.15]; if interval straddles 0.5 => deferred
  - NS Zone       : bootstrap (B=20) -> (T, I, F) -> zone; act only on Consensus

Outputs:
  exp_uci15_results.csv   - one row per (dataset, classifier) with accuracy columns
  exp_uci15_zones.csv     - per-dataset zone distribution
"""
import sys, io, os, csv, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

import numpy as np
from sklearn.datasets import (
    load_iris, load_wine, load_breast_cancer, load_digits, fetch_openml
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.utils import resample
from sklearn.calibration import CalibratedClassifierCV

SEED = 42
B_BOOTSTRAP = 20
N_FOLDS = 5
ALPHA_CONFORMAL = 0.10
IS_HALFWIDTH = 0.15
# Zone thresholds
Z_CONSENSUS = {'T_min': 0.50, 'I_max': 0.35, 'F_max': 0.30}


# ----------------------------------------------------------------------
# Dataset loaders
# ----------------------------------------------------------------------
def load_sklearn_binary(loader, positive_class):
    d = loader()
    X, y = d.data, d.target
    y_bin = (y == positive_class).astype(int)
    return X, y_bin


def load_digits_evenodd():
    d = load_digits()
    return d.data, (d.target % 2).astype(int)


def load_oml(name, version=1, min_class_size=5):
    d = fetch_openml(name, version=version, as_frame=False, parser='liac-arff')
    X = np.asarray(d.data, dtype=float)
    y_raw = d.target
    labels = sorted(set(y_raw.tolist()))
    label_to_idx = {l: i for i, l in enumerate(labels)}
    y = np.array([label_to_idx[v] for v in y_raw])
    # drop rare classes (< min_class_size) to allow stratified CV + calibration split
    counts = np.bincount(y)
    keep_mask = np.isin(y, np.where(counts >= min_class_size)[0])
    X, y = X[keep_mask], y[keep_mask]
    # remap to contiguous ids
    remap = {v: i for i, v in enumerate(sorted(set(y.tolist())))}
    y = np.array([remap[v] for v in y])
    return X, y


DATASETS = [
    ('Iris',         lambda: load_sklearn_binary(load_iris, 0)),          # setosa vs rest
    ('Wine',         lambda: load_sklearn_binary(load_wine, 1)),          # class 1 vs rest
    ('Br. Cancer',   lambda: (load_breast_cancer().data, load_breast_cancer().target)),
    ('Digits',       load_digits_evenodd),
    ('Heart',        lambda: load_oml('heart-statlog')),
    ('Ionosphere',   lambda: load_oml('ionosphere')),
    ('Sonar',        lambda: load_oml('sonar')),
    ('Glass',        lambda: load_oml('glass')),
    ('Vehicle',      lambda: load_oml('vehicle')),
    ('Segment',      lambda: load_oml('segment')),
    ('Vowel',        lambda: load_oml('vowel')),
    ('Yeast',        lambda: load_oml('yeast')),
    ('Ecoli',        lambda: load_oml('ecoli')),
    ('Haberman',     lambda: load_oml('haberman')),
]


# Classifiers (fresh instance each call for reproducibility)
def get_classifiers():
    return [
        ('LR',   LogisticRegression(max_iter=2000, random_state=SEED)),
        ('RF',   RandomForestClassifier(n_estimators=100, random_state=SEED)),
        ('SVM',  SVC(kernel='rbf', probability=True, random_state=SEED)),
        ('KNN',  KNeighborsClassifier(n_neighbors=5)),
        ('NB',   GaussianNB()),
    ]


# ----------------------------------------------------------------------
# Bootstrap T/I/F  (paper-spec adapted for multiclass)
# ----------------------------------------------------------------------
def bootstrap_tif(clf_proto, X_tr, y_tr, X_te, B=B_BOOTSTRAP, seed=SEED):
    """Returns arrays T, I, F, y_hat (point prediction from full-train model),
    plus p_max (probability of predicted class on full model)."""
    rng = np.random.default_rng(seed)

    # Full model point estimate
    clf_full = _clone(clf_proto).fit(X_tr, y_tr)
    p_full = clf_full.predict_proba(X_te)
    y_point = np.argmax(p_full, axis=1)
    p_point = p_full[np.arange(len(X_te)), y_point]   # prob of predicted class

    # Bootstrap predictions
    n = len(X_tr)
    boot_preds = np.zeros((B, len(X_te)), dtype=int)
    boot_probs = np.zeros((B, len(X_te)))  # prob assigned to the *point* class
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        # need at least 2 classes in bootstrap
        if len(np.unique(y_tr[idx])) < 2:
            boot_preds[b] = y_point
            boot_probs[b] = p_point
            continue
        clf_b = _clone(clf_proto).fit(X_tr[idx], y_tr[idx])
        pb = clf_b.predict_proba(X_te)
        # Align columns to classes of full model if needed
        # pb may have different class order
        classes_b = clf_b.classes_
        classes_f = clf_full.classes_
        col_map = {c: i for i, c in enumerate(classes_b)}
        # For each test pt, take prob of "point-predicted class"
        boot_preds[b] = classes_b[np.argmax(pb, axis=1)]
        # translate y_point (indices into classes_f) -> actual class label -> column in pb
        for j, idx_f in enumerate(y_point):
            cls = classes_f[idx_f]
            if cls in col_map:
                boot_probs[b, j] = pb[j, col_map[cls]]
            else:
                boot_probs[b, j] = 0.0

    # Aggregate
    # F: fraction of bootstraps predicting a different class
    F = np.mean(boot_preds != classes_f[y_point], axis=0)
    # I: std of prob across bootstraps, normalized
    I = np.std(boot_probs, axis=0, ddof=0) / 0.5
    I = np.minimum(I, 1.0)
    # T: mean prob of point class (bounded 0-1)
    T = np.clip(np.mean(boot_probs, axis=0), 0.0, 1.0)

    return T, I, F, y_point, p_point


def _clone(est):
    from sklearn.base import clone
    return clone(est)


def ns_zone(T, I, F):
    """Return zone label for each (T,I,F). Vector-safe."""
    zones = np.full(len(T), 'Ignorance', dtype=object)
    # order: Consensus first (most restrictive), then Ambiguity, Contradiction, Ignorance
    cons = (T > Z_CONSENSUS['T_min']) & (I < Z_CONSENSUS['I_max']) & (F < Z_CONSENSUS['F_max'])
    amb  = (I >= Z_CONSENSUS['I_max']) & ~cons
    cont = (T > 0.30) & (F > 0.30) & ~cons & ~amb
    zones[cons] = 'Consensus'
    zones[amb]  = 'Ambiguity'
    zones[cont] = 'Contradiction'
    return zones


# ----------------------------------------------------------------------
# Per (dataset, classifier) benchmark pass
# ----------------------------------------------------------------------
def benchmark_pair(X, y, clf_proto, dataset_name, clf_name):
    # Scale features (helps SVM/KNN/LR)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)

    # Per-point accumulators across folds
    all_y_true = []
    all_y_classical = []
    all_y_platt = []
    all_conf_deferred = []
    all_conf_correct = []
    all_y_is_deferred = []
    all_y_is_correct = []
    all_T, all_I, all_F = [], [], []
    all_y_point = []

    for tr_idx, te_idx in skf.split(X, y):
        X_tr, X_te = X[tr_idx], X[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]

        # --- Classical ---
        clf = _clone(clf_proto).fit(X_tr, y_tr)
        p_te = clf.predict_proba(X_te)
        y_pred_classical = clf.classes_[np.argmax(p_te, axis=1)]
        all_y_true.append(y_te)
        all_y_classical.append(y_pred_classical)

        # --- Platt (CalibratedClassifierCV wraps with sigmoid calibration) ---
        try:
            X_fit, X_cal, y_fit, y_cal = train_test_split(
                X_tr, y_tr, test_size=0.20, stratify=y_tr, random_state=SEED
            )
        except ValueError:
            X_fit, X_cal, y_fit, y_cal = train_test_split(
                X_tr, y_tr, test_size=0.20, random_state=SEED
            )
        try:
            calib = CalibratedClassifierCV(_clone(clf_proto), method='sigmoid', cv='prefit')
            base = _clone(clf_proto).fit(X_fit, y_fit)
            calib.estimator = base
            calib.fit(X_cal, y_cal)
            p_platt = calib.predict_proba(X_te)
            y_pred_platt = calib.classes_[np.argmax(p_platt, axis=1)]
        except Exception:
            # fallback
            y_pred_platt = y_pred_classical
        all_y_platt.append(y_pred_platt)

        # --- Split Conformal ---
        # Calibrate on X_cal; deferred if >1 label in set
        try:
            base_conf = _clone(clf_proto).fit(X_fit, y_fit)
            p_cal = base_conf.predict_proba(X_cal)
            scores_cal = 1 - p_cal[np.arange(len(X_cal)), y_cal]
            q = np.quantile(scores_cal, 1 - ALPHA_CONFORMAL)
            p_te_conf = base_conf.predict_proba(X_te)
            # prediction set: classes with score <= q  (i.e., 1 - prob <= q -> prob >= 1 - q)
            threshold = 1 - q
            pset_size = (p_te_conf >= threshold).sum(axis=1)
            deferred = pset_size != 1
            # accuracy only on kept (|set|==1) points
            conf_pred = base_conf.classes_[np.argmax(p_te_conf, axis=1)]
            correct = (conf_pred == y_te) & (~deferred)
        except Exception:
            deferred = np.zeros(len(y_te), dtype=bool)
            correct = (y_pred_classical == y_te)
        all_conf_deferred.append(deferred)
        all_conf_correct.append(correct)

        # --- Interval Statistics (IS) ---
        p_max = p_te[np.arange(len(X_te)), np.argmax(p_te, axis=1)]
        is_low, is_high = p_max - IS_HALFWIDTH, p_max + IS_HALFWIDTH
        # deferred if interval straddles 0.5 (for binary) or spans > 1 class for multiclass
        # Simpler rule: deferred if is_low < 0.5
        is_deferred = is_low < 0.5
        is_correct = (y_pred_classical == y_te) & (~is_deferred)
        all_y_is_deferred.append(is_deferred)
        all_y_is_correct.append(is_correct)

        # --- NS Zone (bootstrap T/I/F) ---
        T, I, F, y_pt, _ = bootstrap_tif(clf_proto, X_tr, y_tr, X_te, B=B_BOOTSTRAP, seed=SEED)
        y_point_label = clf.classes_[y_pt]
        all_T.append(T); all_I.append(I); all_F.append(F)
        all_y_point.append(y_point_label)

    # Concatenate
    y_true = np.concatenate(all_y_true)
    y_classical = np.concatenate(all_y_classical)
    y_platt = np.concatenate(all_y_platt)
    conf_deferred = np.concatenate(all_conf_deferred)
    conf_correct = np.concatenate(all_conf_correct)
    is_deferred = np.concatenate(all_y_is_deferred)
    is_correct = np.concatenate(all_y_is_correct)
    T = np.concatenate(all_T); I = np.concatenate(all_I); F = np.concatenate(all_F)
    y_point = np.concatenate(all_y_point)

    # Accuracies
    acc_classical = accuracy_score(y_true, y_classical)
    acc_platt     = accuracy_score(y_true, y_platt)
    # Conformal accuracy on kept points
    n_kept_conf = (~conf_deferred).sum()
    acc_conformal = conf_correct.sum() / max(n_kept_conf, 1)
    coverage_conf = n_kept_conf / len(y_true)
    # IS accuracy on kept points
    n_kept_is = (~is_deferred).sum()
    acc_is = is_correct.sum() / max(n_kept_is, 1)
    coverage_is = n_kept_is / len(y_true)

    # NS
    zones = ns_zone(T, I, F)
    acc_ns_all = accuracy_score(y_true, y_point)   # all zones treated as acting
    cons_mask = zones == 'Consensus'
    if cons_mask.sum() > 0:
        acc_ns_cons = accuracy_score(y_true[cons_mask], y_point[cons_mask])
    else:
        acc_ns_cons = 0.0
    coverage_ns = cons_mask.mean()

    # Paraconsistent cases
    n_para = int(((T + F) > 1.0).sum())

    zone_counts = {
        'Consensus':     int((zones == 'Consensus').sum()),
        'Ambiguity':     int((zones == 'Ambiguity').sum()),
        'Contradiction': int((zones == 'Contradiction').sum()),
        'Ignorance':     int((zones == 'Ignorance').sum()),
    }

    return {
        'dataset': dataset_name,
        'clf': clf_name,
        'n': len(y_true),
        'acc_classical': acc_classical,
        'acc_platt': acc_platt,
        'acc_conformal': acc_conformal,
        'cov_conformal': coverage_conf,
        'acc_is': acc_is,
        'cov_is': coverage_is,
        'acc_ns_all': acc_ns_all,
        'acc_ns_cons': acc_ns_cons,
        'cov_ns': coverage_ns,
        'n_paraconsistent': n_para,
        **{f'zone_{k}': v for k, v in zone_counts.items()},
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    out_path = os.path.join(os.path.dirname(__file__), 'exp_uci15_results.csv')
    fieldnames = [
        'dataset', 'clf', 'n',
        'acc_classical', 'acc_platt', 'acc_conformal', 'cov_conformal',
        'acc_is', 'cov_is',
        'acc_ns_all', 'acc_ns_cons', 'cov_ns',
        'n_paraconsistent',
        'zone_Consensus', 'zone_Ambiguity', 'zone_Contradiction', 'zone_Ignorance',
    ]
    rows = []

    print(f"{'Dataset':12s} {'clf':4s} {'n':>5s}  "
          f"{'Class':>6s} {'Platt':>6s} {'Conf':>6s} {'IS':>6s} {'NS_all':>6s} {'NS_cons':>7s} {'cov%':>6s}")
    print('-' * 85)

    for ds_name, loader in DATASETS:
        try:
            X, y = loader()
        except Exception as e:
            print(f"[{ds_name}] load failed: {e}")
            continue
        for clf_name, clf_proto in get_classifiers():
            try:
                res = benchmark_pair(X, y, clf_proto, ds_name, clf_name)
            except Exception as e:
                print(f"[{ds_name}/{clf_name}] failed: {e}")
                continue
            rows.append(res)
            print(f"{ds_name:12s} {clf_name:4s} {res['n']:5d}  "
                  f"{res['acc_classical']:6.3f} {res['acc_platt']:6.3f} "
                  f"{res['acc_conformal']:6.3f} {res['acc_is']:6.3f} "
                  f"{res['acc_ns_all']:6.3f} {res['acc_ns_cons']:7.3f} "
                  f"{res['cov_ns']*100:5.1f}%")

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved: {out_path}  ({len(rows)} rows)")

    # Aggregate per dataset across classifiers (mean)
    agg_path = os.path.join(os.path.dirname(__file__), 'exp_uci15_dataset_means.csv')
    from collections import defaultdict
    by_ds = defaultdict(list)
    for r in rows:
        by_ds[r['dataset']].append(r)

    with open(agg_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['dataset', 'n', 'Classical', 'Platt', 'Conformal', 'IS',
                    'NS_All', 'NS_Cons', 'Coverage', 'n_paraconsistent'])
        for ds, lst in by_ds.items():
            def m(k): return np.mean([r[k] for r in lst])
            w.writerow([
                ds, lst[0]['n'],
                f"{m('acc_classical'):.3f}",
                f"{m('acc_platt'):.3f}",
                f"{m('acc_conformal'):.3f}",
                f"{m('acc_is'):.3f}",
                f"{m('acc_ns_all'):.3f}",
                f"{m('acc_ns_cons'):.3f}",
                f"{m('cov_ns')*100:.1f}%",
                int(np.sum([r['n_paraconsistent'] for r in lst])),
            ])
    print(f"Saved: {agg_path}")


if __name__ == '__main__':
    main()
