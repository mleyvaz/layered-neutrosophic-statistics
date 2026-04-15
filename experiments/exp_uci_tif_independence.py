"""
UCI bootstrap-derived T/I/F independence test.

Loads per-sample T, I, F produced by exp_uci15_benchmark.py-style bootstrapping
but restricted to Logistic Regression (paper: 1 classifier per dataset ≈ 8,940 points).
Computes Pearson r(T,I), r(T,F), r(I,F) and compares against the expert dataset
correlations and the interval counterfactual.
"""
import sys, os, csv, warnings
warnings.filterwarnings('ignore')

import numpy as np
from scipy.stats import pearsonr

# Reuse the loaders and bootstrap_tif from the main benchmark
sys.path.insert(0, os.path.dirname(__file__))
from exp_uci15_benchmark import (
    DATASETS, bootstrap_tif, ns_zone, _clone, SEED, B_BOOTSTRAP
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler


OUT_CSV = os.path.join(os.path.dirname(__file__), 'exp_uci_tif_independence_results.csv')


def compute_tif_for_dataset(X, y, clf_proto):
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    Ts, Is, Fs = [], [], []
    for tr, te in skf.split(X, y):
        T, I, F, _, _ = bootstrap_tif(clf_proto, X[tr], y[tr], X[te], B=B_BOOTSTRAP, seed=SEED)
        Ts.append(T); Is.append(I); Fs.append(F)
    return np.concatenate(Ts), np.concatenate(Is), np.concatenate(Fs)


def main():
    clf_proto = LogisticRegression(max_iter=2000, random_state=SEED)

    all_T, all_I, all_F = [], [], []
    per_ds = []
    for ds_name, loader in DATASETS:
        try:
            X, y = loader()
        except Exception as e:
            print(f"[{ds_name}] load failed: {e}")
            continue
        try:
            T, I, F = compute_tif_for_dataset(X, y, clf_proto)
        except Exception as e:
            print(f"[{ds_name}] T/I/F fail: {e}")
            continue
        rtI, _ = pearsonr(T, I)
        rtF, _ = pearsonr(T, F)
        rIF, _ = pearsonr(I, F)
        per_ds.append({
            'dataset': ds_name, 'n': len(T),
            'r_TI': rtI, 'r_TF': rtF, 'r_IF': rIF,
            'mean_T': T.mean(), 'mean_I': I.mean(), 'mean_F': F.mean(),
        })
        all_T.append(T); all_I.append(I); all_F.append(F)
        print(f"  {ds_name:12s} n={len(T):4d}  "
              f"r(T,I)={rtI:+.3f}  r(T,F)={rtF:+.3f}  r(I,F)={rIF:+.3f}")

    T = np.concatenate(all_T); I = np.concatenate(all_I); F = np.concatenate(all_F)
    N = len(T)
    rtI, _ = pearsonr(T, I)
    rtF, _ = pearsonr(T, F)
    rIF, _ = pearsonr(I, F)
    n_para = int(((T + F) > 1.0).sum())

    print()
    print('=' * 60)
    print(f"UCI bootstrap T,I,F across 14 datasets, LogisticRegression")
    print('=' * 60)
    print(f"  N total          = {N}")
    print(f"  r(T,I) overall   = {rtI:+.4f}")
    print(f"  r(T,F) overall   = {rtF:+.4f}")
    print(f"  r(I,F) overall   = {rIF:+.4f}")
    print(f"  Paraconsistent   = {n_para}  ({n_para/N*100:.1f}%)")

    # Save per-dataset CSV
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['dataset', 'n', 'r_TI', 'r_TF', 'r_IF',
                    'mean_T', 'mean_I', 'mean_F'])
        for r in per_ds:
            w.writerow([r['dataset'], r['n'],
                        f"{r['r_TI']:.4f}", f"{r['r_TF']:.4f}", f"{r['r_IF']:.4f}",
                        f"{r['mean_T']:.4f}", f"{r['mean_I']:.4f}", f"{r['mean_F']:.4f}"])
        w.writerow([])
        w.writerow(['OVERALL', N,
                    f"{rtI:.4f}", f"{rtF:.4f}", f"{rIF:.4f}",
                    f"{T.mean():.4f}", f"{I.mean():.4f}", f"{F.mean():.4f}"])
        w.writerow(['paraconsistent_count', n_para])
    print(f"\nSaved: {OUT_CSV}")


if __name__ == '__main__':
    main()
