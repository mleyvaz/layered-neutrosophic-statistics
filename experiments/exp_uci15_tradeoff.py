# -*- coding: utf-8 -*-
"""
Accuracy-coverage trade-off + zone-threshold sensitivity (reviewer request, HJMS revision)
==========================================================================================
Re-runs the 14-dataset x 5-classifier benchmark of exp_uci15_benchmark.py but saves
PER-POINT outputs (y_true, y_point, p_max, T, I, F), then post-processes:

  A) Confidence-thresholding baseline at MATCHED coverage:
     for each (dataset, clf), choose tau so that coverage(p_max >= tau) equals the
     NS Consensus coverage; report accuracy on kept points. Fair selective-prediction
     comparison requested by both reviewers.
  B) Zone-threshold sensitivity: sweep T_min in {0.45,0.50,0.55}, I_max in {0.30,0.35,0.40},
     F_max in {0.25,0.30,0.35}; report Consensus accuracy & coverage per configuration
     (aggregated over the 70 dataset x classifier pairs).

Outputs:
  exp_uci15_perpoint.csv      per-point raw values
  exp_uci15_tradeoff.csv      per (dataset, clf): NS cons acc/cov vs matched-coverage thresholding
  exp_uci15_sensitivity.csv   27 threshold configs: mean acc, mean coverage
Protocol identical to exp_uci15_benchmark.py: SEED=42, 5-fold stratified CV,
StandardScaler, B=20 bootstrap, sklearn defaults noted in the paper.
"""
import sys, io, os, csv, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits, fetch_openml
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.base import clone

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 42
B_BOOTSTRAP = 20
N_FOLDS = 5

def load_sklearn_binary(loader, positive_class):
    d = loader()
    return d.data, (d.target == positive_class).astype(int)

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
    counts = np.bincount(y)
    keep = np.isin(y, np.where(counts >= min_class_size)[0])
    X, y = X[keep], y[keep]
    remap = {v: i for i, v in enumerate(sorted(set(y.tolist())))}
    return X, np.array([remap[v] for v in y])

DATASETS = [
    ('Iris',       lambda: load_sklearn_binary(load_iris, 0)),
    ('Wine',       lambda: load_sklearn_binary(load_wine, 1)),
    ('Br. Cancer', lambda: (load_breast_cancer().data, load_breast_cancer().target)),
    ('Digits',     load_digits_evenodd),
    ('Heart',      lambda: load_oml('heart-statlog')),
    ('Ionosphere', lambda: load_oml('ionosphere')),
    ('Sonar',      lambda: load_oml('sonar')),
    ('Glass',      lambda: load_oml('glass')),
    ('Vehicle',    lambda: load_oml('vehicle')),
    ('Segment',    lambda: load_oml('segment')),
    ('Vowel',      lambda: load_oml('vowel')),
    ('Yeast',      lambda: load_oml('yeast')),
    ('Ecoli',      lambda: load_oml('ecoli')),
    ('Haberman',   lambda: load_oml('haberman')),
]

def get_classifiers():
    return [
        ('LR',  LogisticRegression(max_iter=2000, random_state=SEED)),
        ('RF',  RandomForestClassifier(n_estimators=100, random_state=SEED)),
        ('SVM', SVC(kernel='rbf', probability=True, random_state=SEED)),
        ('KNN', KNeighborsClassifier(n_neighbors=5)),
        ('NB',  GaussianNB()),
    ]

def bootstrap_tif(clf_proto, X_tr, y_tr, X_te, B=B_BOOTSTRAP, seed=SEED):
    rng = np.random.default_rng(seed)
    clf_full = clone(clf_proto).fit(X_tr, y_tr)
    p_full = clf_full.predict_proba(X_te)
    y_point = np.argmax(p_full, axis=1)
    p_point = p_full[np.arange(len(X_te)), y_point]
    n = len(X_tr)
    boot_preds = np.zeros((B, len(X_te)), dtype=int)
    boot_probs = np.zeros((B, len(X_te)))
    classes_f = clf_full.classes_
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_tr[idx])) < 2:
            boot_preds[b] = classes_f[y_point]
            boot_probs[b] = p_point
            continue
        clf_b = clone(clf_proto).fit(X_tr[idx], y_tr[idx])
        pb = clf_b.predict_proba(X_te)
        classes_b = clf_b.classes_
        col_map = {c: i for i, c in enumerate(classes_b)}
        boot_preds[b] = classes_b[np.argmax(pb, axis=1)]
        for j, idx_f in enumerate(y_point):
            cls = classes_f[idx_f]
            boot_probs[b, j] = pb[j, col_map[cls]] if cls in col_map else 0.0
    F = np.mean(boot_preds != classes_f[y_point], axis=0)
    I = np.minimum(np.std(boot_probs, axis=0, ddof=0) / 0.5, 1.0)
    T = np.clip(np.mean(boot_probs, axis=0), 0.0, 1.0)
    return T, I, F, classes_f[y_point], p_point

rows = []
for ds_name, loader in DATASETS:
    try:
        X, y = loader()
    except Exception as e:
        print(f"SKIP {ds_name}: {e}")
        continue
    X = StandardScaler().fit_transform(X)
    for clf_name, clf_proto in get_classifiers():
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        for tr_idx, te_idx in skf.split(X, y):
            X_tr, X_te = X[tr_idx], X[te_idx]
            y_tr, y_te = y[tr_idx], y[te_idx]
            T, I, F, y_pt, p_max = bootstrap_tif(clf_proto, X_tr, y_tr, X_te)
            for j in range(len(y_te)):
                rows.append((ds_name, clf_name, int(y_te[j]), int(y_pt[j]),
                             round(float(p_max[j]), 5), round(float(T[j]), 5),
                             round(float(I[j]), 5), round(float(F[j]), 5)))
        print(f"done {ds_name} / {clf_name} ({len(rows)} rows cum.)")

with open(os.path.join(HERE, 'exp_uci15_perpoint.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['dataset', 'clf', 'y_true', 'y_point', 'p_max', 'T', 'I', 'F'])
    w.writerows(rows)
print(f"perpoint saved: {len(rows)} rows")

# ---------------- post-processing ----------------
import collections
data = collections.defaultdict(list)
for r in rows:
    data[(r[0], r[1])].append(r)

def zone_mask_consensus(T, I, F, tmin=0.50, imax=0.35, fmax=0.30):
    return (T > tmin) & (I < imax) & (F < fmax)

# A) matched-coverage confidence thresholding
out = []
for (ds, clf), rs in data.items():
    y_true = np.array([r[2] for r in rs]); y_pt = np.array([r[3] for r in rs])
    p = np.array([r[4] for r in rs])
    T = np.array([r[5] for r in rs]); I = np.array([r[6] for r in rs]); F = np.array([r[7] for r in rs])
    cons = zone_mask_consensus(T, I, F)
    cov_ns = cons.mean()
    acc_ns = accuracy_score(y_true[cons], y_pt[cons]) if cons.sum() else np.nan
    # threshold achieving the same coverage on p_max
    if cov_ns >= 1.0:
        tau = -np.inf
    else:
        tau = np.quantile(p, 1.0 - cov_ns)
    keep = p >= tau
    acc_th = accuracy_score(y_true[keep], y_pt[keep]) if keep.sum() else np.nan
    cov_th = keep.mean()
    acc_full = accuracy_score(y_true, y_pt)
    out.append([ds, clf, len(y_true), round(acc_full, 4), round(acc_ns, 4), round(cov_ns, 4),
                round(acc_th, 4), round(cov_th, 4), round(acc_ns - acc_th, 4)])

with open(os.path.join(HERE, 'exp_uci15_tradeoff.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['dataset', 'clf', 'n', 'acc_full', 'acc_ns_cons', 'cov_ns',
                'acc_confthresh_matched', 'cov_confthresh', 'delta_ns_minus_thresh'])
    w.writerows(out)

deltas = [r[8] for r in out if not np.isnan(r[8])]
wins = sum(1 for d in deltas if d > 0); ties = sum(1 for d in deltas if d == 0)
print(f"\nTRADEOFF: mean delta NS-thresh = {np.mean(deltas):+.4f} | NS wins {wins}/{len(deltas)}, ties {ties}")
from scipy.stats import wilcoxon
try:
    stat, pval = wilcoxon(deltas)
    print(f"Wilcoxon NS vs matched thresholding: p = {pval:.4g}")
except Exception as e:
    print("wilcoxon:", e)

# B) sensitivity sweep
sens = []
for tmin in (0.45, 0.50, 0.55):
    for imax in (0.30, 0.35, 0.40):
        for fmax in (0.25, 0.30, 0.35):
            accs, covs = [], []
            for (ds, clf), rs in data.items():
                y_true = np.array([r[2] for r in rs]); y_pt = np.array([r[3] for r in rs])
                T = np.array([r[5] for r in rs]); I = np.array([r[6] for r in rs]); F = np.array([r[7] for r in rs])
                m = zone_mask_consensus(T, I, F, tmin, imax, fmax)
                if m.sum():
                    accs.append(accuracy_score(y_true[m], y_pt[m]))
                    covs.append(m.mean())
            sens.append([tmin, imax, fmax, round(float(np.mean(accs)), 4), round(float(np.mean(covs)), 4)])

with open(os.path.join(HERE, 'exp_uci15_sensitivity.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['T_min', 'I_max', 'F_max', 'mean_consensus_acc', 'mean_coverage'])
    w.writerows(sens)

base = [s for s in sens if s[0] == 0.50 and s[1] == 0.35 and s[2] == 0.30][0]
accs_all = [s[3] for s in sens]; covs_all = [s[4] for s in sens]
print(f"\nSENSITIVITY: baseline acc={base[3]}, cov={base[4]}")
print(f"acc range over 27 configs: [{min(accs_all)}, {max(accs_all)}] | cov range: [{min(covs_all)}, {max(covs_all)}]")
print("DONE")
