"""
Friedman test + Nemenyi post-hoc on exp_uci15_results.csv.

Compares NS Consensus vs Classical, Platt, Conformal, IS across
14 datasets (rows) × 5 methods (columns) averaged over 5 classifiers.
Also produces per-classifier pairwise tests and mean-rank diagrams.
"""
import sys, io, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
from scipy.stats import friedmanchisquare, rankdata, wilcoxon, norm
from collections import defaultdict


HERE = os.path.dirname(__file__)
INPUT = os.path.join(HERE, 'exp_uci15_results.csv')
OUTPUT = os.path.join(HERE, 'exp_uci15_statistical_tests.csv')


def load():
    rows = []
    with open(INPUT, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def nemenyi_cd(k, n, q_alpha):
    """Critical difference = q_alpha * sqrt(k*(k+1)/(6n))."""
    return q_alpha * np.sqrt(k * (k + 1) / (6.0 * n))


# Nemenyi q-values at alpha=0.05 (studentized range / sqrt(2))
# Source: Demšar (2006) Table 5
Q_ALPHA_05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}


def friedman_nemenyi(data_matrix, labels):
    """data_matrix: n_datasets × k_methods. Returns dict with stats."""
    n, k = data_matrix.shape
    # Friedman
    stat, p = friedmanchisquare(*[data_matrix[:, j] for j in range(k)])
    # Ranks per row (higher accuracy -> rank 1)
    # rankdata gives rank 1 for smallest -> invert: rank on -x
    ranks = np.array([rankdata(-row, method='average') for row in data_matrix])
    mean_ranks = ranks.mean(axis=0)
    # Nemenyi critical difference
    q = Q_ALPHA_05.get(k, 3.164)
    cd = nemenyi_cd(k, n, q)
    # Pairwise differences significant?
    pairwise = {}
    for i in range(k):
        for j in range(i + 1, k):
            diff = abs(mean_ranks[i] - mean_ranks[j])
            pairwise[(labels[i], labels[j])] = {
                'mean_rank_diff': diff,
                'significant_at_0.05': diff > cd,
            }
    return {
        'n_datasets': n,
        'k_methods': k,
        'friedman_chi2': float(stat),
        'friedman_p': float(p),
        'mean_ranks': dict(zip(labels, mean_ranks.tolist())),
        'cd_005': float(cd),
        'pairwise': pairwise,
    }


def wilcoxon_vs_ns(data_matrix, labels, ns_idx):
    """Wilcoxon signed-rank: each method vs NS Consensus."""
    out = {}
    ns = data_matrix[:, ns_idx]
    for j, lab in enumerate(labels):
        if j == ns_idx:
            continue
        diffs = ns - data_matrix[:, j]
        if np.all(diffs == 0):
            out[lab] = {'W': 0, 'p': 1.0}
        else:
            try:
                stat, p = wilcoxon(ns, data_matrix[:, j], zero_method='wilcox')
                out[lab] = {'W': float(stat), 'p': float(p)}
            except Exception:
                out[lab] = {'W': np.nan, 'p': np.nan}
    return out


def main():
    rows = load()
    # Group by (dataset, clf) -> row. We want a matrix averaged across classifiers
    # per dataset × method (for the main Friedman).
    by_ds = defaultdict(list)
    for r in rows:
        by_ds[r['dataset']].append(r)

    datasets = sorted(by_ds.keys(),
                      key=lambda d: ['Iris','Wine','Br. Cancer','Digits','Heart',
                                     'Ionosphere','Sonar','Glass','Vehicle','Segment',
                                     'Vowel','Yeast','Ecoli','Haberman'].index(d)
                      if d in ['Iris','Wine','Br. Cancer','Digits','Heart','Ionosphere',
                               'Sonar','Glass','Vehicle','Segment','Vowel','Yeast','Ecoli','Haberman']
                      else 999)

    methods = ['acc_classical', 'acc_platt', 'acc_conformal', 'acc_is', 'acc_ns_cons']
    labels  = ['Classical', 'Platt', 'Conformal', 'IS', 'NS Cons']

    mat = np.zeros((len(datasets), len(methods)))
    for i, ds in enumerate(datasets):
        for j, m in enumerate(methods):
            mat[i, j] = float(np.mean([float(r[m]) for r in by_ds[ds]]))

    print("Accuracy matrix (rows=datasets, cols=methods, mean across 5 classifiers):")
    print(f"{'Dataset':12s} " + ''.join([f"{l:>10s}" for l in labels]))
    for i, ds in enumerate(datasets):
        print(f"{ds:12s} " + ''.join([f"{mat[i,j]:>10.3f}" for j in range(len(methods))]))
    print()

    result = friedman_nemenyi(mat, labels)
    print("=" * 70)
    print("Friedman test (across 14 datasets × 5 methods)")
    print("=" * 70)
    print(f"  chi^2 = {result['friedman_chi2']:.3f}")
    print(f"  p     = {result['friedman_p']:.2e}")
    print(f"  Mean ranks (1 = best):")
    for lab, r in sorted(result['mean_ranks'].items(), key=lambda kv: kv[1]):
        print(f"    {lab:12s} {r:5.2f}")
    print(f"  Nemenyi CD (alpha=0.05): {result['cd_005']:.3f}")
    print(f"  Pairwise significance vs NS Cons:")
    for (a, b), v in result['pairwise'].items():
        if 'NS Cons' in (a, b):
            other = a if b == 'NS Cons' else b
            print(f"    NS Cons vs {other:12s}  mean_rank_diff={v['mean_rank_diff']:.2f}  "
                  f"sig={v['significant_at_0.05']}")

    print()
    print("Wilcoxon signed-rank: NS Cons vs each other method (14 datasets):")
    w = wilcoxon_vs_ns(mat, labels, ns_idx=4)
    for lab, v in w.items():
        print(f"  NS Cons vs {lab:12s}  W={v['W']}  p={v['p']:.4f}")

    # Per-classifier Friedman
    print()
    print("=" * 70)
    print("Per-classifier Friedman (within each classifier, 5 methods × 14 datasets)")
    print("=" * 70)
    per_clf = {}
    clfs = ['LR', 'RF', 'SVM', 'KNN', 'NB']
    for clf in clfs:
        mat_clf = np.zeros((len(datasets), len(methods)))
        for i, ds in enumerate(datasets):
            recs = [r for r in by_ds[ds] if r['clf'] == clf]
            if not recs:
                continue
            for j, m in enumerate(methods):
                mat_clf[i, j] = float(recs[0][m])
        res = friedman_nemenyi(mat_clf, labels)
        per_clf[clf] = res
        print(f"  {clf}: chi^2={res['friedman_chi2']:.2f}  p={res['friedman_p']:.2e}  "
              f"NS rank={res['mean_ranks']['NS Cons']:.2f}  "
              f"Class rank={res['mean_ranks']['Classical']:.2f}")

    # Save summary CSV
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['scope', 'friedman_chi2', 'friedman_p', 'cd_005',
                    'rank_Classical', 'rank_Platt', 'rank_Conformal', 'rank_IS', 'rank_NSCons'])
        def row(scope, r):
            mr = r['mean_ranks']
            w.writerow([scope, f"{r['friedman_chi2']:.4f}", f"{r['friedman_p']:.4e}",
                        f"{r['cd_005']:.4f}",
                        f"{mr['Classical']:.3f}", f"{mr['Platt']:.3f}",
                        f"{mr['Conformal']:.3f}", f"{mr['IS']:.3f}", f"{mr['NS Cons']:.3f}"])
        row('all_mean_across_clfs', result)
        for clf in clfs:
            if clf in per_clf:
                row(f'per_clf_{clf}', per_clf[clf])
    print(f"\nSaved: {OUTPUT}")

    # Mean improvement NS Cons vs Classical
    print()
    diffs = mat[:, 4] - mat[:, 0]
    print(f"Mean accuracy gain NS Cons − Classical = {diffs.mean()*100:+.2f} pp")
    print(f"Median gain = {np.median(diffs)*100:+.2f} pp  (14 datasets)")


if __name__ == '__main__':
    main()
