# Woodall Response — Experiments

Code, data, and figures accompanying the two-part response to:

> Woodall, W. H., King, C., Driscoll, A. R., & Montgomery, D. C. (2025). *A critical assessment of neutrosophic statistics.*

**Authors:** Maikel Y. Leyva-Vázquez¹ and Florentin Smarandache²
¹ Universidad de Guayaquil, Ecuador · ² University of New Mexico, USA

## Companion papers

- **Part I — Theory:** *Clarifying the Layers of Neutrosophic Statistics — A Taxonomy and Publication Protocol*
- **Part II — Empirical:** *A Corrected Simulation and Extended Empirical Evidence*

## Repository layout

```
experiments/
  # Part I (Response / Taxonomy paper)
  exp1_indeterminacy_reduction.py   # NS vs IS under 1,000 operations
  exp2_tif_independence.py          # T/I/F independence — expert data
  exp3_head_to_head.py              # Classical vs Interval vs Neutrosophic (10 hypotheses)
  exp4_uci_ns_benchmark.py          # 5-dataset NS benchmark (sanity check)
  exp5_corrected_simulation.py      # Elasticity + zone classification (matches Paper A §3)

  # Part II (UCI Benchmark paper) — full experiments
  exp_uci15_benchmark.py            # 14 UCI × 5 classifiers × {Classical, Platt, Conformal, IS, NS}
  exp_uci15_statistical_tests.py    # Friedman + Nemenyi + per-classifier + Wilcoxon
  exp_uci_tif_independence.py       # UCI bootstrap T/I/F across 14 datasets (LR)
  exp_expert_annotation.py          # 22 experts × 30 hypotheses study (Fleiss κ, NS vs Classical vs IS)
  parse_expert_xlsx.py              # Optional: regenerate exp_expert_long.csv from local raw xlsx
  exp_50_hypotheses.py              # Earlier synthetic pilot (superseded by expert study)
  gen_paper_b_figures.py            # Regenerates figures 5-8 from the CSVs
  gen_expert_figure.py              # Fig 4: expert-study confusion matrix + method comparison

  # Outputs (all seeded, reproducible)
  exp1_results.csv, exp2_results.csv, exp3_results.csv, exp4_results.csv,
  exp5_results.json,
  exp_uci15_results.csv, exp_uci15_dataset_means.csv,
  exp_uci15_statistical_tests.csv,
  exp_uci_tif_independence_results.csv,
  exp_50_hypotheses_results.csv, exp_50_hypotheses_results_summary.csv

figures/                            # All figures referenced in both papers
```

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

Each script is self-contained, seeded (`random.seed(42)` / `np.random.seed(42)`), and writes its CSV/JSON output next to the script.

## Experiments summary

### Part I (Paper A — Response / Taxonomy)

| # | File | Claim validated |
|---|------|-----------------|
| 1 | exp1_indeterminacy_reduction.py | NS intervals are 1.37–1.54× narrower than IS; IS never wins in 2,000 ops |
| 2 | exp2_tif_independence.py | Expert T/I/F data has \|r\| < 0.10; interval-disguised counter-factual \|r\| > 0.6 |
| 3 | exp3_head_to_head.py | 10-hypothesis head-to-head: zone classification separates decisions |
| 4 | exp4_uci_ns_benchmark.py | 5-dataset sanity check (Iris, Wine, BC, Digits, Wine neg. ctrl) |
| 5 | exp5_corrected_simulation.py | Elasticity (NS ≡ classical ANOVA at I=0) + zone shifts as I grows |

### Part II (Paper B — UCI Benchmark)

| File | Output | Claim validated |
|------|--------|-----------------|
| exp_uci15_benchmark.py | `exp_uci15_results.csv`, `exp_uci15_dataset_means.csv` | 14 UCI × 5 clfs: NS Cons. accuracy gain +6.4 pp vs Classical |
| exp_uci15_statistical_tests.py | `exp_uci15_statistical_tests.csv` | Friedman χ² = 44.55, p < 10⁻⁸; NS Cons. significantly beats Classical & Platt (Wilcoxon p = 0.0015) |
| exp_uci_tif_independence.py | `exp_uci_tif_independence_results.csv` | Bootstrap T/I/F shows strong algebraic correlations (\|r\| ≈ 0.5–0.7); independence holds only for expert T/I/F |
| exp_expert_annotation.py | `exp_expert_long.csv`, `exp_expert_aggregated.csv`, `exp_expert_summary.csv` | 22 experts × 30 hypotheses, 660 triplets: Fleiss κ = 0.06 (low agreement on labels), NS 83.3% CI [66, 93], Classical 30.0%, Interval 3-way 93.3%, McNemar χ² = 10.23 (p = 0.0014), paraconsistency 38.8% |
| exp_50_hypotheses.py | `exp_50_hypotheses_results*.csv` | Earlier synthetic pilot, superseded — kept for reproducibility of draft numbers |
| gen_paper_b_figures.py | `figures/Fig5–Fig8.png` | Figures regenerated from the CSVs |

## Data provenance

The expert annotation data (`experiments/exp_expert_long.csv`) contains 22 domain
experts' (T, I, F) responses for 30 causal hypotheses, collected via a structured
online form (Google Forms). The file is anonymized: only sequential `expert_id`
(1..22) and `hypothesis_id` (1..30) are retained, with the original timestamps
stripped. Raters consented to anonymous publication of their aggregated responses.
The raw xlsx is not included in the repository; researchers with the raw file can
regenerate the CSV with `parse_expert_xlsx.py`.

## License

MIT — see `LICENSE`.

## Citation

If you use this code, please cite both Part I and Part II.
