"""
Expert-annotated (T, I, F) study.

Reads the anonymized long-format CSV (22 experts × 30 causal hypotheses),
T, I, F on a 0–10 scale. Produces:
 - Per-hypothesis aggregated (mean T, mean I, mean F, SDs)
 - Zone classification per (expert × hypothesis), modal zone per hypothesis
 - Inter-rater agreement: Fleiss' kappa on zones (appropriate for 22 raters)
 - T/I/F correlations on the 660 triplets
 - NS zone accuracy of the aggregated (mean) triplet vs modal ground-truth
 - Paraconsistency rate (T + F > 1 on normalized scale)

The long CSV is committed to the repo (already anonymized: expert_id 1..22, no PII).
The original Google-Forms xlsx is NOT shared to protect rater anonymity.
If you have the raw xlsx locally, use parse_expert_xlsx.py to regenerate the CSV.
"""
import sys, os, csv, math
import numpy as np
from scipy.stats import pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
LONG_CSV = os.path.join(HERE, 'exp_expert_long.csv')
AGG_CSV = os.path.join(HERE, 'exp_expert_aggregated.csv')
SUM_CSV = os.path.join(HERE, 'exp_expert_summary.csv')


# Zone thresholds (normalized 0–1 scale)
def zone_of(T, I, F):
    if T > 0.50 and I < 0.35 and F < 0.30:
        return 'Consensus'
    if I >= 0.35:
        return 'Ambiguity'
    if T > 0.30 and F > 0.30:
        return 'Contradiction'
    return 'Ignorance'


ZONES = ['Consensus', 'Ambiguity', 'Contradiction', 'Ignorance']


def fleiss_kappa(matrix):
    """matrix: N items × k categories; values are rater counts per category.
    Each row sums to the number of raters (same for all rows)."""
    N, k = matrix.shape
    n_raters = matrix.sum(axis=1)
    assert np.all(n_raters == n_raters[0]), "All items must have same # raters"
    n = int(n_raters[0])

    P_i = (np.sum(matrix * matrix, axis=1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    p_j = matrix.sum(axis=0) / (N * n)
    P_e = float(np.sum(p_j ** 2))
    if P_e == 1.0:
        return 1.0
    return (P_bar - P_e) / (1.0 - P_e)


def main():
    if not os.path.exists(LONG_CSV):
        sys.exit(f"Input CSV not found: {LONG_CSV}\n"
                 f"If you have the raw xlsx, run parse_expert_xlsx.py first.")

    long_rows = []
    with open(LONG_CSV, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            for k in ('T_0_10','I_0_10','F_0_10','T','I','F'):
                r[k] = float(r[k])
            for k in ('expert_id','hypothesis_id','paraconsistent'):
                r[k] = int(r[k])
            long_rows.append(r)

    experts = sorted(set(r['expert_id'] for r in long_rows))
    hyps = sorted(set(r['hypothesis_id'] for r in long_rows))
    n_experts, n_hyp = len(experts), len(hyps)
    hyp_labels = [None] * n_hyp
    for r in long_rows:
        hyp_labels[r['hypothesis_id'] - 1] = r['hypothesis']

    print(f"Loaded: {n_experts} experts × {n_hyp} hypotheses  "
          f"→ {len(long_rows)} (expert, hypothesis) triplets")

    # Correlations on the full long data (660 triplets)
    T = np.array([r['T'] for r in long_rows])
    I = np.array([r['I'] for r in long_rows])
    F = np.array([r['F'] for r in long_rows])
    rtI, _ = pearsonr(T, I)
    rtF, _ = pearsonr(T, F)
    rIF, _ = pearsonr(I, F)
    n_para = int(((T + F) > 1.0).sum())

    print(f"\nCorrelations (all {len(T)} triplets):")
    print(f"  r(T,I) = {rtI:+.4f}")
    print(f"  r(T,F) = {rtF:+.4f}")
    print(f"  r(I,F) = {rIF:+.4f}")
    print(f"  Paraconsistent (T+F>1): {n_para}  ({n_para/len(T)*100:.1f}%)")

    # Per-hypothesis aggregates
    agg = []
    per_hyp_zones = {h: [] for h in range(1, n_hyp + 1)}
    for r in long_rows:
        per_hyp_zones[r['hypothesis_id']].append(r['zone'])

    for h_id in range(1, n_hyp + 1):
        subset = [r for r in long_rows if r['hypothesis_id'] == h_id]
        if not subset:
            continue
        mT = np.mean([r['T'] for r in subset])
        mI = np.mean([r['I'] for r in subset])
        mF = np.mean([r['F'] for r in subset])
        zones = per_hyp_zones[h_id]
        # Modal zone (ground truth)
        from collections import Counter
        counts = Counter(zones)
        modal = counts.most_common(1)[0][0]
        zone_agg = zone_of(mT, mI, mF)
        agg.append({
            'hypothesis_id': h_id,
            'hypothesis': hyp_labels[h_id - 1],
            'n_raters': len(subset),
            'mean_T': round(mT, 4), 'mean_I': round(mI, 4), 'mean_F': round(mF, 4),
            'sd_T': round(float(np.std([r['T'] for r in subset], ddof=1)), 4),
            'sd_I': round(float(np.std([r['I'] for r in subset], ddof=1)), 4),
            'sd_F': round(float(np.std([r['F'] for r in subset], ddof=1)), 4),
            'modal_zone': modal,
            'zone_of_mean': zone_agg,
            'ns_correct': int(zone_agg == modal),
            'pct_consensus': round(counts.get('Consensus', 0) / len(zones), 3),
            'pct_ambiguity': round(counts.get('Ambiguity', 0) / len(zones), 3),
            'pct_contradiction': round(counts.get('Contradiction', 0) / len(zones), 3),
            'pct_ignorance': round(counts.get('Ignorance', 0) / len(zones), 3),
        })

    with open(AGG_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)
    print(f"  Saved: {AGG_CSV}")

    # Fleiss' kappa on zone labels (N=30 items × k=4 categories × n=22 raters)
    ck = np.zeros((n_hyp, len(ZONES)), dtype=int)
    for h_id in range(1, n_hyp + 1):
        zs = per_hyp_zones[h_id]
        for z in zs:
            ck[h_id - 1, ZONES.index(z)] += 1
    # ensure each row sums to number of raters that actually responded
    row_sums = ck.sum(axis=1)
    if not np.all(row_sums == row_sums[0]):
        # pad: only keep rows with same number of raters
        mode = int(np.bincount(row_sums).argmax())
        keep = row_sums == mode
        ck = ck[keep]
        print(f"  Note: using {keep.sum()} hypotheses with complete responses "
              f"({mode} raters each) for Fleiss' kappa")
    kappa = fleiss_kappa(ck)
    print(f"\nFleiss' kappa (22 raters × 30 items × 4 zones): {kappa:.4f}")

    # NS accuracy: zone of mean = modal zone
    ns_correct = sum(r['ns_correct'] for r in agg)
    ns_acc = ns_correct / len(agg)

    # Classical binary: support if mean T > mean F
    cls_correct = 0
    for r in agg:
        cls_pred = 'support' if r['mean_T'] > r['mean_F'] else 'not_support'
        cls_gt = ('support' if r['modal_zone'] in ('Consensus', 'Contradiction')
                  else 'not_support')
        if cls_pred == cls_gt:
            cls_correct += 1
    cls_acc = cls_correct / len(agg)

    # Interval 3-way
    iv_correct = 0
    for r in agg:
        T_, I_, F_ = r['mean_T'], r['mean_I'], r['mean_F']
        lo, hi = T_ - I_, T_ + I_
        if lo > 0.5:
            iv_pred = 'support'
        elif hi < 0.5:
            iv_pred = 'not_support'
        else:
            iv_pred = 'inconclusive'
        iv_gt = {'Consensus': 'support', 'Ignorance': 'not_support',
                 'Ambiguity': 'inconclusive',
                 'Contradiction': 'inconclusive'}[r['modal_zone']]
        if iv_pred == iv_gt:
            iv_correct += 1
    iv_acc = iv_correct / len(agg)

    print(f"\nAccuracy (aggregated mean TIF vs modal ground truth):")
    print(f"  NS zone        : {ns_acc*100:.1f}%  ({ns_correct}/{len(agg)})")
    print(f"  Classical 2-way: {cls_acc*100:.1f}%  ({cls_correct}/{len(agg)})")
    print(f"  Interval 3-way : {iv_acc*100:.1f}%  ({iv_correct}/{len(agg)})")

    # Wilson CI for NS
    from scipy.stats import norm
    z = norm.ppf(0.975)
    p = ns_acc; N = len(agg)
    denom = 1 + z**2 / N
    center = (p + z**2 / (2 * N)) / denom
    half = z * math.sqrt(p*(1-p)/N + z**2 / (4*N**2)) / denom
    print(f"  NS 95% Wilson CI: [{(center-half)*100:.1f}%, {(center+half)*100:.1f}%]")

    # McNemar NS vs Classical
    b = sum(1 for r in agg if r['ns_correct'] and
            (('support' if r['mean_T'] > r['mean_F'] else 'not_support') !=
             ('support' if r['modal_zone'] in ('Consensus', 'Contradiction') else 'not_support')))
    c = sum(1 for r in agg if not r['ns_correct'] and
            (('support' if r['mean_T'] > r['mean_F'] else 'not_support') ==
             ('support' if r['modal_zone'] in ('Consensus', 'Contradiction') else 'not_support')))
    if (b + c) > 0:
        chi2_mc = (abs(b - c) - 1)**2 / (b + c)
        from scipy.stats import chi2 as chi2_dist
        p_mc = 1 - chi2_dist.cdf(chi2_mc, df=1)
    else:
        chi2_mc, p_mc = 0.0, 1.0
    print(f"  McNemar NS vs Classical: chi^2={chi2_mc:.2f}  p={p_mc:.4e}")

    # Summary CSV
    with open(SUM_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value'])
        w.writerow(['n_experts', n_experts])
        w.writerow(['n_hypotheses', n_hyp])
        w.writerow(['n_triplets', len(long_rows)])
        w.writerow(['r_TI', f'{rtI:.4f}'])
        w.writerow(['r_TF', f'{rtF:.4f}'])
        w.writerow(['r_IF', f'{rIF:.4f}'])
        w.writerow(['fleiss_kappa', f'{kappa:.4f}'])
        w.writerow(['ns_accuracy', f'{ns_acc:.4f}'])
        w.writerow(['classical_accuracy', f'{cls_acc:.4f}'])
        w.writerow(['interval_accuracy', f'{iv_acc:.4f}'])
        w.writerow(['mcnemar_chi2', f'{chi2_mc:.4f}'])
        w.writerow(['mcnemar_p', f'{p_mc:.4e}'])
        w.writerow(['paraconsistent_count', n_para])
        w.writerow(['paraconsistent_pct', f'{n_para/len(T)*100:.2f}'])
    print(f"\n  Saved: {SUM_CSV}")


if __name__ == '__main__':
    main()
