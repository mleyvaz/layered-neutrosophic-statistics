# Layered Neutrosophic Statistics — Experiments

Code, data, and figures supporting the paper:

> **Smarandache, F.; Leyva-Vázquez, M. Y.** *A Layered Framework for Neutrosophic Statistics: Foundational Distinctions, Empirical Validation, and Operational Implementation.* Under review, **Hacettepe Journal of Mathematics and Statistics**, 2026 (manuscript 1942616).

**Preprint of an earlier version (Zenodo):** [https://doi.org/10.5281/zenodo.19778334](https://doi.org/10.5281/zenodo.19778334)

**Authors:**
- Florentin Smarandache¹ — Mathematics, Physics and Natural Science Division, University of New Mexico, Gallup, NM, USA · `smarand@unm.edu`
- Maikel Y. Leyva-Vázquez² — Universidad Bolivariana del Ecuador / Universidad de Guayaquil, Ecuador · `maikel.leyvav@ug.edu.ec`

---

## What this paper presents

Neutrosophic statistics is organized as a **layered framework**, with each layer corresponding to a distinct mathematical regime and decision-theoretic role:

- **Layer 1 — Neutrosophic arithmetic** (`N = a + bI`): a determinate part plus an indeterminate component that need not be an interval (hesitant sets, thick functions, refined indeterminacy); interval projection is shown to be a lossy compression.
- **Layer 2 — Neutrosophic set statistics** (`(T, I, F)`): truth, indeterminacy, and falsity as three representational degrees of freedom, admitting paraconsistent states `T + F > 1`.
- **Layer 3 — Plithogenic statistics**: generalizes both via the degree of appurtenance for multi-attribute aggregation.

The paper provides six lines of theoretical and empirical validation, including an interval-reducibility test on real expert-annotated data, head-to-head and UCI benchmarks against classical, calibration, conformal, and confidence-thresholding baselines, and layer-selection diagnostics.

---

## Repository layout

```
experiments/
  exp1_indeterminacy_reduction.py     # NS vs IS under repeated operations
  exp2_tif_independence.py            # (T,I,F) structure on expert data vs interval counter-factual (Sec. 3.2)
  exp3_head_to_head.py                # Classical vs Interval vs Neutrosophic on 10 causal hypotheses (Sec. 3.3)
  exp4_uci_ns_benchmark.py            # 5-dataset UCI benchmark (Sec. 3.5)
  exp5_corrected_simulation.py        # Elasticity property and zone classification under varying I

  exp_uci15_benchmark.py              # Extended 14 UCI x 5 classifiers benchmark (Sec. 3.7)
  exp_uci15_statistical_tests.py      # Friedman + Nemenyi + Wilcoxon
  exp_uci15_tradeoff.py               # Matched-coverage confidence-thresholding baseline +
                                      #   27-configuration zone-threshold sensitivity sweep (Sec. 3.7)
  exp_uci_tif_independence.py         # UCI bootstrap T,I,F across 14 datasets
  exp_expert_annotation.py            # 22 raters x 30 hypotheses annotation study
  exp_expert_filter.py                # Pre-specified rater filtering (drop bottom 5 by modal agreement)
  parse_expert_xlsx.py                # Regenerate expert long-form CSV from raw xlsx (optional)
  exp_50_hypotheses.py                # Synthetic pilot (superseded; retained for traceability)
  gen_paper_b_figures.py              # Benchmark figures
  gen_expert_figure.py                # Expert-study confusion matrix

  exp1..exp5 results (CSV/JSON),
  exp_uci15_results.csv, exp_uci15_dataset_means.csv, exp_uci15_statistical_tests.csv,
  exp_uci15_perpoint.csv, exp_uci15_tradeoff.csv, exp_uci15_sensitivity.csv,
  exp_expert_long.csv (660 triplets), exp_expert_filtered_long.csv (510 triplets),
  exp_expert_agreement_ranking.csv, exp_expert_*_summary.csv

figures/                              # All figures referenced in the paper
```

---

## How to reproduce

```bash
python -m venv .venv
# Windows:   .venv\Scripts\activate
# macOS/Lin: source .venv/bin/activate
pip install -r requirements.txt

python experiments/exp1_indeterminacy_reduction.py
python experiments/exp2_tif_independence.py
python experiments/exp3_head_to_head.py
python experiments/exp4_uci_ns_benchmark.py
python experiments/exp5_corrected_simulation.py
python experiments/exp_uci15_benchmark.py
python experiments/exp_uci15_tradeoff.py
```

Each script is self-contained, seeded (seed 42; bootstrap replicates use seeds `42+b`), and writes its CSV or JSON output next to the script. Verified environment: Python 3.14, NumPy 2.4, SciPy 1.17, scikit-learn 1.8 (Windows 11, CPU only).

---

## Experiments summary

| # | File | Result |
|---|------|--------|
| 1 | `exp1_indeterminacy_reduction.py` | NS intervals are 1.37–1.54x narrower than IS; IS does not improve under 2,000 sequential operations |
| 2 | `exp2_tif_independence.py` + `exp_expert_filter.py` | On the 510 quality-filtered expert triplets: r(T,I) = −0.176 (3.4x weaker than the −0.601 forced by the interval-derived counter-factual), r(I,F) = +0.295 (opposite sign), paraconsistency 34.9% (0% by construction in the counter-factual) |
| 3 | `exp3_head_to_head.py` | 10-hypothesis head-to-head: zone classification 90% vs 20% for binary verdicts; on the full 30 hypotheses, 96.7% (29/30) vs 40%, McNemar p = 1.0e-4 |
| 4 | `exp4_uci_ns_benchmark.py` | 5-dataset UCI benchmark: Consensus-zone accuracy 0.973–1.000 at 79–99% coverage |
| 5 | `exp5_corrected_simulation.py` | Elasticity: NS coincides with classical ANOVA when `I = 0`; zones shift predictably as `I` grows |

### Extended benchmark, selective-prediction comparison, and expert study

| File | Output | Result |
|------|--------|--------|
| `exp_uci15_benchmark.py` | `exp_uci15_results.csv`, `..._dataset_means.csv` | 14 UCI x 5 classifiers: NS Consensus +6.4 pp over Classical (0.883 vs 0.819) at mean coverage 0.768 |
| `exp_uci15_statistical_tests.py` | `exp_uci15_statistical_tests.csv` | Friedman chi-squared = 44.55, p < 1e-8; NS Consensus beats Classical and Platt (Wilcoxon, Bonferroni-corrected) |
| `exp_uci15_tradeoff.py` | `exp_uci15_perpoint.csv`, `..._tradeoff.csv`, `..._sensitivity.csv` | At coverage exactly matched per pair, NS Consensus beats confidence thresholding by +1.0 pp on average (Wilcoxon p = 0.048; largest gains: Yeast +5.6 pp, Digits +2.7 pp). Threshold sensitivity over 27 configs: accuracy 0.872–0.895, coverage 0.723–0.811, monotone |
| `exp_expert_annotation.py` + `exp_expert_filter.py` | `exp_expert_long.csv`, `exp_expert_filtered_*.csv` | 22 raters x 30 hypotheses (660 triplets); pre-specified filtering drops the 5 raters with modal agreement < 0.50, retaining 17 raters (510 triplets). Fleiss kappa 0.06 unfiltered / 0.18 filtered; mean modal agreement 63.8% → 75.5% |
| `exp_uci_tif_independence.py` | `exp_uci_tif_independence_results.csv` | Bootstrap-derived T,I,F shows strong algebraic correlations; the structural diagnostics separate genuine expert triplets from derived ones |

---

## Data provenance

The expert annotation data (`experiments/exp_expert_long.csv`) contains 22 raters' `(T, I, F)` responses for 30 causal hypotheses on a 0.1-step scale, collected through a structured online form, blind to model outputs. The file is anonymized: only sequential `expert_id` (1..22) and `hypothesis_id` (1..30) are retained, with timestamps stripped. Raters consented to anonymous publication of their aggregated responses. The quality-filtered dataset (`exp_expert_filtered_long.csv`, 510 triplets) is produced by `exp_expert_filter.py` under a pre-specified criterion. The raw xlsx is not included; researchers with the raw file can regenerate the CSV with `parse_expert_xlsx.py`.

---

## Citation

If you use this code or data, please cite the paper and the Zenodo deposit:

```bibtex
@article{smarandache_leyvavazquez_2026_layered,
  author  = {Smarandache, Florentin and Leyva-V{\'a}zquez, Maikel Y.},
  title   = {A Layered Framework for Neutrosophic Statistics: Foundational
             Distinctions, Empirical Validation, and Operational Implementation},
  journal = {Hacettepe Journal of Mathematics and Statistics},
  year    = {2026},
  note    = {Under review, manuscript 1942616}
}

@dataset{smarandache_leyvavazquez_2025_zenodo,
  author    = {Smarandache, Florentin and Leyva-V{\'a}zquez, Maikel Y.},
  title     = {Layered Neutrosophic Statistics: Empirical Validation and Operational Implementation},
  year      = {2025},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19778334},
  url       = {https://doi.org/10.5281/zenodo.19778334}
}
```

---

## License

MIT — see `LICENSE`.
