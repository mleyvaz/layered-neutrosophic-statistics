# Layered Neutrosophic Symmetry — Experiments

Code, data, and figures supporting the paper:

> **Smarandache, F.; Leyva-Vázquez, M. Y.** *Symmetry and Asymmetry in Layered Neutrosophic Statistics: A Framework for Uncertainty Modeling and Intelligent Decision-Making.* Submitted to the Special Issue *Symmetry in Uncertainty and Intelligent Decision-Making*, **Symmetry** (MDPI), 2026.

**Preprint (Zenodo):** [https://doi.org/10.5281/zenodo.19778334](https://doi.org/10.5281/zenodo.19778334)

**Authors:**
- Florentin Smarandache¹ — Mathematics, Physics and Natural Science Division, University of New Mexico, Gallup, NM, USA · `smarand@unm.edu`
- Maikel Y. Leyva-Vázquez² — Faculty of Mathematical and Physical Sciences, Universidad de Guayaquil, Ecuador · `maikel.leyvav@ug.edu.ec`

---

## What this paper presents

Neutrosophic statistics is presented as a **layered framework** for representing uncertainty in intelligent decision-making, in which each layer corresponds to a distinct symmetry regime:

- **Layer 1 — Neutrosophic arithmetic** (`N = a + bI`): preserves classical arithmetic symmetries in the determinate part while explicitly breaking symmetry in the indeterminate part.
- **Layer 2 — Neutrosophic set statistics** (`(T, I, F)`): breaks reciprocity between truth and falsity in a controlled way, allowing structurally independent dimensions.
- **Layer 3 — Plithogenic statistics**: generalizes both via the asymmetric construct of degree of appurtenance.

The paper provides five lines of empirical and theoretical validation supporting the claim that interval and bivalent representations impose excessive symmetry on data that is structurally asymmetric.

---

## Repository layout

```
experiments/
  exp1_indeterminacy_reduction.py     # NS vs IS under repeated operations (Section 3.1)
  exp2_tif_independence.py            # T,I,F independence on expert-annotated data (Section 3.2)
  exp3_head_to_head.py                # Classical vs Interval vs Neutrosophic on 10 causal hypotheses (Section 3.3)
  exp4_uci_ns_benchmark.py            # 5-dataset UCI benchmark (Section 3.5)
  exp5_corrected_simulation.py        # Elasticity property and zone classification under varying I

  exp_uci15_benchmark.py              # Extended 14 UCI x 5 classifiers benchmark
  exp_uci15_statistical_tests.py      # Friedman + Nemenyi + Wilcoxon
  exp_uci_tif_independence.py         # UCI bootstrap T,I,F across 14 datasets
  exp_expert_annotation.py            # 22 experts x 30 hypotheses annotation study
  parse_expert_xlsx.py                # Regenerate expert long-form CSV from raw xlsx (optional)
  exp_50_hypotheses.py                # Synthetic pilot (superseded; retained for traceability)
  gen_paper_b_figures.py              # Figures 5-8
  gen_expert_figure.py                # Figure 4: expert-study confusion matrix

  exp1_results.csv, exp2_results.csv, exp3_results.csv, exp4_results.csv,
  exp5_results.json,
  exp_uci15_results.csv, exp_uci15_dataset_means.csv,
  exp_uci15_statistical_tests.csv,
  exp_uci_tif_independence_results.csv,
  exp_50_hypotheses_results.csv, exp_50_hypotheses_results_summary.csv

figures/                              # All figures referenced in the paper
```

---

## How to reproduce

```bash
python -m venv .venv
# Windows:   .venv\Scripts\activate
# macOS/Lin: source .venv/bin/activate
pip install -r requirements.txt

# Run each experiment individually
python experiments/exp1_indeterminacy_reduction.py
python experiments/exp2_tif_independence.py
python experiments/exp3_head_to_head.py
python experiments/exp4_uci_ns_benchmark.py
python experiments/exp5_corrected_simulation.py
```

Each script is self-contained, seeded (`random.seed(42)` / `np.random.seed(42)`), and writes its CSV or JSON output next to the script.

---

## Experiments summary

| # | File | Claim validated |
|---|------|-----------------|
| 1 | `exp1_indeterminacy_reduction.py` | NS intervals are 1.37–1.54x narrower than IS; IS does not improve under 2,000 sequential operations |
| 2 | `exp2_tif_independence.py` | Expert T,I,F data shows \|r\| < 0.10; interval-derived counter-factual triplets show \|r\| > 0.60 — confirms structural asymmetry |
| 3 | `exp3_head_to_head.py` | 10-hypothesis head-to-head benchmark: zone classification achieves 90% accuracy vs binary methods that give misleading verdicts on 8 of 10 |
| 4 | `exp4_uci_ns_benchmark.py` | 5-dataset UCI benchmark (Iris, Wine, BC, Digits, Wine negative control): Consensus-zone accuracy 0.973–1.000 with 79–99% coverage |
| 5 | `exp5_corrected_simulation.py` | Elasticity property: NS coincides with classical ANOVA when `I = 0`; zones shift predictably as `I` grows |

### Extended benchmark and expert study

| File | Output | Claim validated |
|------|--------|-----------------|
| `exp_uci15_benchmark.py` | `exp_uci15_results.csv`, `exp_uci15_dataset_means.csv` | 14 UCI x 5 classifiers: NS Consensus accuracy gain of +6.4 pp over Classical |
| `exp_uci15_statistical_tests.py` | `exp_uci15_statistical_tests.csv` | Friedman chi-squared = 44.55, p < 10^-8; NS Consensus beats Classical and Platt (Wilcoxon p = 0.0015) |
| `exp_uci_tif_independence.py` | `exp_uci_tif_independence_results.csv` | Bootstrap T,I,F shows strong algebraic correlations (\|r\| ~ 0.5–0.7); structural independence holds only for genuine expert-annotated T,I,F |
| `exp_expert_annotation.py` | `exp_expert_long.csv`, `exp_expert_aggregated.csv`, `exp_expert_summary.csv` | 22 experts x 30 hypotheses, 660 triplets: Fleiss kappa = 0.06; NS 83.3% CI [66, 93]; Classical 30.0%; Interval three-way 93.3%; McNemar chi-squared = 10.23 (p = 0.0014); paraconsistency rate 38.8% |
| `exp_50_hypotheses.py` | `exp_50_hypotheses_results*.csv` | Earlier synthetic pilot, superseded by the expert study; retained for traceability |
| `gen_paper_b_figures.py` | `figures/Fig5–Fig8.png` | Figures regenerated from the CSVs |

---

## Data provenance

The expert annotation data (`experiments/exp_expert_long.csv`) contains 22 domain experts' `(T, I, F)` responses for 30 causal hypotheses, collected through a structured online form. The file is anonymized: only sequential `expert_id` (1..22) and `hypothesis_id` (1..30) are retained, with timestamps stripped. Raters consented to anonymous publication of their aggregated responses. The raw xlsx is not included; researchers with the raw file can regenerate the CSV with `parse_expert_xlsx.py`.

---

## Citation

If you use this code or data, please cite the paper and the Zenodo deposit:

```bibtex
@article{smarandache_leyvavazquez_2026_symmetry,
  author  = {Smarandache, Florentin and Leyva-V{\'a}zquez, Maikel Y.},
  title   = {Symmetry and Asymmetry in Layered Neutrosophic Statistics:
             A Framework for Uncertainty Modeling and Intelligent Decision-Making},
  journal = {Symmetry},
  year    = {2026},
  note    = {Special Issue: Symmetry in Uncertainty and Intelligent Decision-Making}
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
