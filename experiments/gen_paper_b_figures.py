"""
Regenerates Paper B figures (5, 6, 7, 8) from the new benchmark CSVs.
Also regenerates Fig 2 (T/I/F scatter) and Fig 3 (correlation forest).

Output: Papers/figures/*.png
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
FIG_DIR = os.path.join(REPO_ROOT, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)


# Dataset ordering (Paper B Table 1)
DS_ORDER = ['Iris', 'Wine', 'Br. Cancer', 'Digits', 'Heart', 'Ionosphere',
            'Sonar', 'Glass', 'Vehicle', 'Segment', 'Vowel', 'Yeast',
            'Ecoli', 'Haberman']


def load_means():
    path = os.path.join(HERE, 'exp_uci15_dataset_means.csv')
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    rows.sort(key=lambda r: DS_ORDER.index(r['dataset']) if r['dataset'] in DS_ORDER else 99)
    return rows


def load_full():
    path = os.path.join(HERE, 'exp_uci15_results.csv')
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            for k in ['acc_classical','acc_platt','acc_conformal','acc_is',
                      'acc_ns_all','acc_ns_cons','cov_ns']:
                r[k] = float(r[k])
            rows.append(r)
    return rows


def fig5_accuracy_comparison(means):
    """Fig 5. Panel A: Classical vs NS Cons accuracy bar chart.
       Panel B: per-dataset improvement (Δ)."""
    datasets = [r['dataset'] for r in means]
    classical = np.array([float(r['Classical']) for r in means])
    ns_cons   = np.array([float(r['NS_Cons']) for r in means])
    delta     = (ns_cons - classical) * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    # Panel A
    x = np.arange(len(datasets))
    w = 0.35
    axes[0].bar(x - w/2, classical, w, label='Classical', color='#1f77b4')
    axes[0].bar(x + w/2, ns_cons,  w, label='NS Consensus', color='#2ca02c')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(datasets, rotation=40, ha='right', fontsize=9)
    axes[0].set_ylabel('Accuracy')
    axes[0].set_title('A. Classical vs NS Consensus accuracy (14 datasets)')
    axes[0].set_ylim(0.0, 1.05)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)

    # Panel B
    axes[1].bar(x, delta, color=['#2ca02c' if d >= 0 else '#d62728' for d in delta])
    axes[1].axhline(delta.mean(), color='black', linestyle='--',
                    label=f'mean = {delta.mean():+.2f} pp')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(datasets, rotation=40, ha='right', fontsize=9)
    axes[1].set_ylabel('Δ Accuracy (pp)')
    axes[1].set_title('B. Per-dataset improvement (NS Cons − Classical)')
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, 'Fig5_Accuracy_Comparison.png')
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  {out}")


def fig6_coverage_accuracy(full):
    """Fig 6. Coverage vs accuracy for 3 representative datasets
    (Breast Cancer, Digits, Wine), as we vary the NS Consensus threshold."""
    # For each dataset, compute classical and NS-cons accuracy per-classifier and average
    # Simple rendering: plot (coverage, NS-cons accuracy) per classifier, plus classical.
    subsets = ['Br. Cancer', 'Digits', 'Wine']
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, ds in zip(axes, subsets):
        recs = [r for r in full if r['dataset'] == ds]
        if not recs:
            continue
        covs = np.array([r['cov_ns'] for r in recs]) * 100
        accs = np.array([r['acc_ns_cons'] for r in recs])
        cla  = np.array([r['acc_classical'] for r in recs])
        # Sort by coverage
        order = np.argsort(covs)
        ax.plot(covs[order], accs[order], 'o-', color='#2ca02c', label='NS Consensus')
        ax.axhline(cla.mean(), color='gray', linestyle='--',
                   label=f'Classical mean ({cla.mean():.3f})')
        ax.set_xlabel('Coverage (%)')
        ax.set_ylabel('Accuracy')
        ax.set_title(f'{ds}')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        ax.set_ylim(0.5, 1.02)
    plt.suptitle('Coverage–accuracy tradeoff (5 classifiers per dataset)', fontsize=12)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, 'Fig6_Coverage_Accuracy.png')
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  {out}")


def fig7_zone_distribution(full):
    """Fig 7. Zone distribution per dataset (stacked bars)."""
    by_ds = {}
    for r in full:
        ds = r['dataset']
        by_ds.setdefault(ds, {'cons':0,'amb':0,'cont':0,'ign':0})
        for src, dst in [('zone_Consensus','cons'), ('zone_Ambiguity','amb'),
                         ('zone_Contradiction','cont'), ('zone_Ignorance','ign')]:
            by_ds[ds][dst] += int(r[src])

    datasets = [d for d in DS_ORDER if d in by_ds]
    cons = np.array([by_ds[d]['cons'] for d in datasets], float)
    amb  = np.array([by_ds[d]['amb']  for d in datasets], float)
    cont = np.array([by_ds[d]['cont'] for d in datasets], float)
    ign  = np.array([by_ds[d]['ign']  for d in datasets], float)
    tot  = cons + amb + cont + ign
    cons_p = cons / tot * 100
    amb_p  = amb  / tot * 100
    cont_p = cont / tot * 100
    ign_p  = ign  / tot * 100

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(datasets))
    ax.bar(x, cons_p, color='#2ca02c', label='Consensus')
    ax.bar(x, amb_p, bottom=cons_p, color='#ff7f0e', label='Ambiguity')
    ax.bar(x, cont_p, bottom=cons_p + amb_p, color='#d62728', label='Contradiction')
    ax.bar(x, ign_p, bottom=cons_p + amb_p + cont_p, color='#7f7f7f', label='Ignorance')
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, rotation=40, ha='right', fontsize=9)
    ax.set_ylabel('% of test points')
    ax.set_title('Zone distribution across 14 UCI datasets (5 classifiers combined)')
    ax.legend(loc='lower right')
    ax.set_ylim(0, 100)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, 'Fig7_Zone_Distribution.png')
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  {out}")


def fig8_classifier_ranks(full):
    """Fig 8. Per-classifier mean accuracy rank of each method."""
    clfs = ['LR', 'RF', 'SVM', 'KNN', 'NB']
    methods = [('acc_classical','Classical'), ('acc_platt','Platt'),
               ('acc_conformal','Conformal'), ('acc_is','IS'),
               ('acc_ns_cons','NS Cons')]
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.15
    x = np.arange(len(clfs))
    for i, (key, lab) in enumerate(methods):
        ranks = []
        for clf in clfs:
            recs = [r for r in full if r['clf'] == clf]
            if not recs:
                ranks.append(np.nan)
                continue
            # per-dataset: rank methods by accuracy (1=best)
            from collections import defaultdict
            from scipy.stats import rankdata
            by_ds = defaultdict(list)
            for r in recs:
                by_ds[r['dataset']].append(r)
            mat = []
            for ds, lst in by_ds.items():
                row = [float(lst[0][m]) for m, _ in methods]
                mat.append(row)
            mat = np.array(mat)
            row_ranks = np.array([rankdata(-r, method='average') for r in mat])
            ranks.append(row_ranks[:, i].mean())
        color = '#2ca02c' if lab == 'NS Cons' else None
        ax.bar(x + (i - 2)*width, ranks, width, label=lab, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(clfs)
    ax.set_ylabel('Mean rank (1 = best)')
    ax.set_title('Mean accuracy rank per classifier (14 datasets, 5 methods)')
    ax.invert_yaxis()  # so rank=1 at top
    ax.legend(loc='lower right')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, 'Fig8_Classifier_Ranks.png')
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  {out}")


def main():
    means = load_means()
    full = load_full()
    print("Generating Paper B figures:")
    fig5_accuracy_comparison(means)
    fig6_coverage_accuracy(full)
    fig7_zone_distribution(full)
    fig8_classifier_ranks(full)
    print("Done.")


if __name__ == '__main__':
    main()
