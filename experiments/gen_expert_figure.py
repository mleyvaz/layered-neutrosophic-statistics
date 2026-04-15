"""Generate Fig 4 for Paper B: expert data confusion matrix + method comparison."""
import os, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(os.path.dirname(HERE), 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

# Load aggregated results
agg = []
with open(os.path.join(HERE, 'exp_expert_aggregated.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        agg.append(r)

# Load summary
summary = {}
with open(os.path.join(HERE, 'exp_expert_summary.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        summary[r['metric']] = r['value']

ZONES = ['Consensus', 'Ambiguity', 'Contradiction', 'Ignorance']

# Build confusion matrix: rows=modal, cols=zone_of_mean
cm = np.zeros((4, 4), dtype=int)
for r in agg:
    i = ZONES.index(r['modal_zone'])
    j = ZONES.index(r['zone_of_mean'])
    cm[i, j] += 1

# Panel A: confusion matrix
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
im = axes[0].imshow(cm, cmap='Greens', vmin=0)
axes[0].set_xticks(range(4)); axes[0].set_yticks(range(4))
axes[0].set_xticklabels(ZONES, rotation=30, ha='right')
axes[0].set_yticklabels(ZONES)
axes[0].set_xlabel('Predicted zone (from mean T,I,F)')
axes[0].set_ylabel('Modal zone across 22 experts (ground truth)')
axes[0].set_title(f"A. NS confusion matrix  ({int(summary['n_hypotheses'])} hypotheses, "
                  f"accuracy = {float(summary['ns_accuracy'])*100:.1f}%)")
for i in range(4):
    for j in range(4):
        axes[0].text(j, i, str(cm[i, j]), ha='center', va='center',
                     color='white' if cm[i, j] > cm.max()/2 else 'black', fontsize=11)
plt.colorbar(im, ax=axes[0], fraction=0.045)

# Panel B: method comparison
methods = ['NS zone', 'Classical 2-way', 'Interval 3-way']
accs = [float(summary['ns_accuracy']),
        float(summary['classical_accuracy']),
        float(summary['interval_accuracy'])]
colors = ['#2ca02c', '#1f77b4', '#ff7f0e']
bars = axes[1].bar(methods, [a * 100 for a in accs], color=colors)
axes[1].set_ylabel('Accuracy (%)')
axes[1].set_ylim(0, 100)
axes[1].set_title(f"B. Method comparison  (n={summary['n_hypotheses']} hypotheses, "
                  f"N={summary['n_experts']} experts)")
axes[1].grid(axis='y', alpha=0.3)
for bar, a in zip(bars, accs):
    axes[1].text(bar.get_x() + bar.get_width()/2, a*100 + 2,
                 f'{a*100:.1f}%', ha='center', fontsize=11)
# McNemar annotation
axes[1].text(0.5, -14,
             f"McNemar NS vs Classical: χ² = {float(summary['mcnemar_chi2']):.2f}, "
             f"p = {float(summary['mcnemar_p']):.2e}",
             transform=axes[1].transData, ha='center', fontsize=9, color='dimgray')

plt.tight_layout()
out = os.path.join(FIG_DIR, 'Fig4_Expert_Study.png')
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out}")
