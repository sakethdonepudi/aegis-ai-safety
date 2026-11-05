# SciFact Evaluation Analysis

## Dataset and split

- **Dataset:** SciFact release archive (`data.tar.gz`), CC BY-NC 2.0.
- **Archive SHA-256:** `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`
- **Corpus:** 5,183 abstracts, imported into Db2 as 9,242 passages in 15.45 s.
- **Split:** The official test split has no public evidence labels. The labelled
  **dev** split was used as the held-out set. AEGIS never trained on SciFact.
- **Subset:** Balanced 100 claims (34 SUPPORTED / 33 CONTRADICTED / 33
  INSUFFICIENT_EVIDENCE), deterministic selection from the 300 labelled dev claims.
- **Label mapping:** `SUPPORT` → `SUPPORTED`, `CONTRADICT` → `CONTRADICTED`, `NEI` →
  `INSUFFICIENT_EVIDENCE`.

## Pipeline

1. All abstracts imported with `SOURCE_TYPE='scifact'` and `EXTERNAL_ID` = original
   SciFact doc ID.
2. All passages loaded from Db2 once into a full-corpus BM25 index.
3. Top 10 passages retrieved per claim; top 4 passed to the verifier.
4. Gold labels and gold document IDs are used only for scoring/Recall@K; they are
   never given to retrieval or the verifier.
5. Model: local Ollama `qwen2.5:7b-instruct`, temperature 0, max 450 tokens.
6. Guardrails: citation validation, numeric checks, evidence-term overlap, and
   missing-evidence abstention.

## Results

| Metric | Value |
| --- | ---: |
| Claims evaluated | 100 |
| Coverage / errors | 1.0 / 0 |
| Accuracy | 0.630 |
| Macro precision | 0.648 |
| Macro recall | 0.629 |
| **Macro F1** | **0.615** |
| SUPPORTED precision / recall / F1 | 0.727 / 0.706 / 0.716 |
| CONTRADICTED precision / recall / F1 | 0.667 / 0.364 / 0.471 |
| INSUFFICIENT precision / recall / F1 | 0.551 / 0.818 / 0.659 |
| Retrieval Recall@1 / @3 / @5 / @10 | 0.57 / 0.71 / 0.77 / 0.80 |
| Mean / median / p95 latency | 24.93 s / 22.36 s / 43.61 s |
| Total measured claim processing | 2,499.9 s |

Confusion matrix (gold rows / predicted columns):

| Gold \ Pred | Supported | Contradicted | Insufficient |
| --- | ---: | ---: | ---: |
| Supported | 24 | 3 | 7 |
| Contradicted | 6 | 12 | 15 |
| Insufficient | 3 | 3 | 27 |

False positives: 6 of 33 NEI claims were given a definitive label (3 supported, 3
contradicted). Contradicted recall is the main weakness; 15/33 contradicted claims were
abstained on.

## Baseline comparison

Measured on the same balanced 20-claim subset, same model/temperature, top-4 retrieved
passages for B and AEGIS. Source: `reports/scifact_baselines.json`.

| Approach | Evidence | Accuracy | Macro precision | Macro recall | Macro F1 |
| --- | --- | ---: | ---: | ---: | ---: |
| A — LLM only | none | 0.500 | 0.544 | 0.500 | 0.509 |
| B — LLM + retrieved passages | top 4 | 0.700 | 0.793 | 0.714 | 0.692 |
| AEGIS — complete pipeline | top 4 | 0.700 | 0.730 | 0.706 | **0.701** |

A has no access to the source abstracts, so its weaker score measures model memory and
not retrieval. B and AEGIS receive identical retrieved passages; AEGIS adds citation
validation, numeric checks, evidence-overlap guarding, and missing-evidence handling.
AEGIS's macro F1 is 0.009 above B on 20 claims, while B has higher macro precision
(0.793 vs 0.730). This is a small, non-significant difference—not evidence of
superiority. AEGIS improves contradiction recall (0.571 vs 0.429) but trades some
precision. The 20-claim subset is too small for a strong claim.

The comparison does not isolate each guardrail. A proper ablation (citation validation
removed, numeric checks removed, overlap guard removed) is future work.

## Baseline comparison (20-claim subset)

| Approach | Accuracy | Macro F1 |
| --- | ---: | ---: |
| LLM only, no evidence | 0.500 | 0.509 |
| LLM + retrieved passages | 0.700 | 0.692 |
| AEGIS complete pipeline | 0.700 | 0.701 |

AEGIS's advantage over the evidence-only baseline is small (0.009 macro F1 on 20
claims) and not statistically significant. See `reports/scifact_baselines.json`.

## Interpretation

**Revision note:** the 100-claim metrics above were measured before the final QA
guardrails (percent-override safety, entity-aware numeric matching, boilerplate/relevance
guard, and conflict prompt). The 40-case suite was rerun after those fixes (33/40 →
38/40); the full 100-claim SciFact benchmark was not rerun. The numbers should therefore
be read as the measured baseline for commit `70bd714`, not as final post-fix benchmark
performance.

- This is development-set performance on a 100-claim subset, not the hidden-label test
  split and not a statistically significant comparison.
- Retrieval Recall@10 = 0.80 means at least 20% of claims cannot be supported by the
  supplied top-10 passages regardless of model quality.
- The model is conservative: NEI recall is high (0.818) but contradiction recall is
  low (0.364). This is preferable to false certainty but limits usefulness for
  refutation.
- SciFact claims are single sentences over abstracts; AEGIS's production PDF path and
  numeric checks are not fully exercised by this benchmark.

## Reproducibility

```bash
make scifact-data
python experiments/run_scifact_eval.py --import --limit 100 --model qwen2.5:7b-instruct
```

Outputs: `experiments/predictions/scifact_dev_predictions.jsonl`,
`experiments/results/scifact_dev_metrics.json`,
`experiments/results/scifact_doc_map.json`.
