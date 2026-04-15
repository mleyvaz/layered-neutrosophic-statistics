"""
Trim the lowest-agreement experts and re-run the analysis.

Strategy:
  1. Compute modal zone across all 22 experts per hypothesis (provisional GT).
  2. For each expert, agreement rate = fraction of 30 hypotheses where their
     zone matches the provisional modal zone.
  3. Rank experts, identify the low-agreement group.
  4. Remove them; recompute modal zones on the remaining experts;
     re-run correlations, Fleiss, accuracy, McNemar, paraconsistency.

Default cut: bottom 25% (5 experts removed, 17 retained).
Set TRIM_BOTTOM_N env var or edit the constant below to change.
"""
import os, csv, math
import numpy as np
from scipy.stats import pearsonr, chi2 as chi2_dist, norm
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LONG_CSV = os.path.join(HERE, 'exp_expert_long.csv')
OUT_LONG = os.path.join(HERE, 'exp_expert_filtered_long.csv')
OUT_AGG = os.path.join(HERE, 'exp_expert_filtered_aggregated.csv')
OUT_SUM = os.path.join(HERE, 'exp_expert_filtered_summary.csv')
OUT_RANK = os.path.join(HERE, 'exp_expert_agreement_ranking.csv')

TRIM_BOTTOM_N = int(os.environ.get('TRIM_BOTTOM_N', 5))   # number of experts to drop

ZONES = ['Consensus', 'Ambiguity', 'Contradiction', 'Ignorance']


def zone_of(T, I, F):
    if T > 0.50 and I < 0.35 and F < 0.30:
        return 'Consensus'
    if I >= 0.35:
        return 'Ambiguity'
    if T > 0.30 and F > 0.30:
        return 'Contradiction'
    return 'Ignorance'


def fleiss_kappa(matrix):
    N, k = matrix.shape
    n_raters = matrix.sum(axis=1)
    assert np.all(n_raters == n_raters[0])
    n = int(n_raters[0])
    P_i = (np.sum(matrix * matrix, axis=1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    p_j = matrix.sum(axis=0) / (N * n)
    P_e = float(np.sum(p_j ** 2))
    return (P_bar - P_e) / (1.0 - P_e) if P_e < 1.0 else 1.0


def modal_zones(rows, experts):
    per_hyp = defaultdict(list)
    for r in rows:
        if r['expert_id'] in experts:
            per_hyp[r['hypothesis_id']].append(r['zone'])
    return {h: Counter(zs).most_common(1)[0][0] for h, zs in per_hyp.items()}


def main():
    rows = []
    with open(LONG_CSV, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            for k in ('T_0_10', 'I_0_10', 'F_0_10', 'T', 'I', 'F'):
                r[k] = float(r[k])
            for k in ('expert_id', 'hypothesis_id', 'paraconsistent'):
                r[k] = int(r[k])
            rows.append(r)

    all_experts = sorted({r['expert_id'] for r in rows})
    all_hyps    = sorted({r['hypothesis_id'] for r in rows})
    print(f"Start: {len(all_experts)} experts × {len(all_hyps)} hypotheses  "
          f"({len(rows)} triplets)")

    # Provisional modal zones from all 22
    modal = modal_zones(rows, set(all_experts))

    # Per-expert agreement with provisional modal
    agree = {}
    for e in all_experts:
        correct = sum(1 for r in rows
                      if r['expert_id'] == e and r['zone'] == modal[r['hypothesis_id']])
        total   = sum(1 for r in rows if r['expert_id'] == e)
        agree[e] = correct / total if total else 0.0

    # Rank and show
    ranked = sorted(agree.items(), key=lambda kv: kv[1])
    print("\nExpert agreement with provisional modal (lowest first):")
    for i, (e, a) in enumerate(ranked):
        tag = ' ← drop' if i < TRIM_BOTTOM_N else ''
        print(f"  expert {e:2d}  agreement = {a*100:5.1f}%{tag}")
    with open(OUT_RANK, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['expert_id', 'agreement_with_provisional_modal', 'dropped'])
        for i, (e, a) in enumerate(ranked):
            w.writerow([e, f'{a:.4f}', int(i < TRIM_BOTTOM_N)])
    print(f"  Saved: {OUT_RANK}")

    drop_ids = {e for e, _ in ranked[:TRIM_BOTTOM_N]}
    keep_ids = [e for e in all_experts if e not in drop_ids]
    kept_rows = [r for r in rows if r['expert_id'] in keep_ids]

    print(f"\nAfter trim: {len(keep_ids)} experts × {len(all_hyps)} hypotheses  "
          f"({len(kept_rows)} triplets)  [dropped {len(drop_ids)} experts: "
          f"{sorted(drop_ids)}]")

    # Save filtered long
    with open(OUT_LONG, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(kept_rows)

    # Re-compute everything on kept set
    new_modal = modal_zones(kept_rows, set(keep_ids))

    # Correlations
    T = np.array([r['T'] for r in kept_rows])
    I = np.array([r['I'] for r in kept_rows])
    F = np.array([r['F'] for r in kept_rows])
    rtI, _ = pearsonr(T, I)
    rtF, _ = pearsonr(T, F)
    rIF, _ = pearsonr(I, F)
    n_para = int(((T + F) > 1.0).sum())

    # Fleiss kappa on the kept experts' zone votes
    ck = np.zeros((len(all_hyps), len(ZONES)), dtype=int)
    for r in kept_rows:
        ck[r['hypothesis_id'] - 1, ZONES.index(r['zone'])] += 1
    row_sums = ck.sum(axis=1)
    if not np.all(row_sums == row_sums[0]):
        mode = int(np.bincount(row_sums).argmax())
        ck = ck[row_sums == mode]
        print(f"(Fleiss using {ck.shape[0]} hypotheses with complete responses, "
              f"{mode} raters each)")
    kappa = fleiss_kappa(ck)

    # Per-hypothesis aggregates (means) on kept set
    agg = []
    for h in all_hyps:
        subset = [r for r in kept_rows if r['hypothesis_id'] == h]
        if not subset:
            continue
        mT = np.mean([r['T'] for r in subset])
        mI = np.mean([r['I'] for r in subset])
        mF = np.mean([r['F'] for r in subset])
        zones_h = [r['zone'] for r in subset]
        modal_h = Counter(zones_h).most_common(1)[0][0]
        zm = zone_of(mT, mI, mF)
        agg.append({
            'hypothesis_id': h,
            'hypothesis': subset[0]['hypothesis'],
            'n_raters': len(subset),
            'mean_T': round(mT, 4), 'mean_I': round(mI, 4), 'mean_F': round(mF, 4),
            'modal_zone': modal_h,
            'zone_of_mean': zm,
            'ns_correct': int(zm == modal_h),
        })

    with open(OUT_AGG, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)

    N = len(agg)
    ns_correct = sum(r['ns_correct'] for r in agg)
    ns_acc = ns_correct / N

    # Classical 2-way
    cls_correct = 0
    for r in agg:
        pred = 'support' if r['mean_T'] > r['mean_F'] else 'not_support'
        gt   = ('support' if r['modal_zone'] in ('Consensus', 'Contradiction')
                else 'not_support')
        if pred == gt:
            cls_correct += 1
    cls_acc = cls_correct / N

    # Interval 3-way
    iv_correct = 0
    for r in agg:
        lo, hi = r['mean_T'] - r['mean_I'], r['mean_T'] + r['mean_I']
        if lo > 0.5: pred = 'support'
        elif hi < 0.5: pred = 'not_support'
        else: pred = 'inconclusive'
        gt = {'Consensus': 'support', 'Ignorance': 'not_support',
              'Ambiguity': 'inconclusive', 'Contradiction': 'inconclusive'}[r['modal_zone']]
        if pred == gt:
            iv_correct += 1
    iv_acc = iv_correct / N

    # McNemar NS vs Classical
    b = c = 0
    for r in agg:
        ns_right = r['ns_correct']
        cls_pred = 'support' if r['mean_T'] > r['mean_F'] else 'not_support'
        cls_gt   = ('support' if r['modal_zone'] in ('Consensus', 'Contradiction')
                    else 'not_support')
        cls_right = cls_pred == cls_gt
        if ns_right and not cls_right: b += 1
        if not ns_right and cls_right: c += 1
    if b + c > 0:
        chi2_mc = (abs(b - c) - 1) ** 2 / (b + c)
        p_mc = 1 - chi2_dist.cdf(chi2_mc, df=1)
    else:
        chi2_mc, p_mc = 0.0, 1.0

    # Wilson CI for NS
    z = norm.ppf(0.975)
    p_hat = ns_acc
    denom = 1 + z**2 / N
    center = (p_hat + z**2 / (2 * N)) / denom
    half = z * math.sqrt(p_hat*(1-p_hat)/N + z**2/(4*N**2)) / denom

    # Summary
    print("\n" + "=" * 70)
    print(f"FILTERED RESULTS ({len(keep_ids)} experts × {N} hypotheses, "
          f"{len(kept_rows)} triplets)")
    print("=" * 70)
    print(f"Correlations (n={len(kept_rows)}):")
    print(f"  r(T,I) = {rtI:+.4f}")
    print(f"  r(T,F) = {rtF:+.4f}")
    print(f"  r(I,F) = {rIF:+.4f}")
    print(f"Paraconsistent (T+F>1): {n_para} ({n_para/len(kept_rows)*100:.1f}%)")
    print(f"Fleiss' kappa: {kappa:.4f}")
    print()
    print(f"Accuracy:")
    print(f"  NS zone        : {ns_acc*100:.1f}%  ({ns_correct}/{N})  "
          f"95% CI [{(center-half)*100:.1f}%, {(center+half)*100:.1f}%]")
    print(f"  Classical 2-way: {cls_acc*100:.1f}%  ({cls_correct}/{N})")
    print(f"  Interval 3-way : {iv_acc*100:.1f}%  ({iv_correct}/{N})")
    print(f"McNemar NS vs Classical: chi^2 = {chi2_mc:.2f}  p = {p_mc:.4e}")

    with open(OUT_SUM, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value'])
        w.writerow(['trim_bottom_n', TRIM_BOTTOM_N])
        w.writerow(['experts_retained', len(keep_ids)])
        w.writerow(['triplets', len(kept_rows)])
        w.writerow(['n_hypotheses', N])
        w.writerow(['fleiss_kappa', f'{kappa:.4f}'])
        w.writerow(['r_TI', f'{rtI:.4f}'])
        w.writerow(['r_TF', f'{rtF:.4f}'])
        w.writerow(['r_IF', f'{rIF:.4f}'])
        w.writerow(['paraconsistent_count', n_para])
        w.writerow(['paraconsistent_pct', f'{n_para/len(kept_rows)*100:.2f}'])
        w.writerow(['ns_accuracy', f'{ns_acc:.4f}'])
        w.writerow(['ns_ci_low', f'{center-half:.4f}'])
        w.writerow(['ns_ci_high', f'{center+half:.4f}'])
        w.writerow(['classical_accuracy', f'{cls_acc:.4f}'])
        w.writerow(['interval_accuracy', f'{iv_acc:.4f}'])
        w.writerow(['mcnemar_chi2', f'{chi2_mc:.4f}'])
        w.writerow(['mcnemar_p', f'{p_mc:.4e}'])
    print(f"\n  Saved: {OUT_SUM}")


if __name__ == '__main__':
    main()
