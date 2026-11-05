# Experiments — Evaluation Foundation

This directory prepares reproducible SciFact evaluation. **No benchmark has been run,
and no result is reported here.**

## Dataset: SciFact

- **Source:** https://github.com/allenai/scifact and
  https://huggingface.co/datasets/allenai/scifact
- **Version:** HuggingFace `allenai/scifact`; record the exact revision/commit when
  downloading for a frozen evaluation. Split sizes: 1,261 train / 450 validation /
  300 test claims; 5,183 corpus abstracts.
- **License:** **CC BY-NC 2.0** (https://creativecommons.org/licenses/by-nc/2.0/).
  The dataset is not redistributed in this repository and must not be used commercially.
- **Citation:** Wadden et al. (2020), *Fact or Fiction: Verifying Scientific Claims*,
  EMNLP 2020.
- **Labels:** `SUPPORT` → `SUPPORTED`, `CONTRADICT` → `CONTRADICTED`, `NEI` →
  `INSUFFICIENT_EVIDENCE`.

Manifest: [`scifact_manifest.json`](scifact_manifest.json).

## Files

| File | Purpose |
| --- | --- |
| `scifact_loader.py` | Load official JSONL/JSON claims exports; derive labels and cited docs |
| `metrics.py` | Macro F1, per-class precision/recall, confusion matrix, FP analysis, Recall@K, latency |
| `evaluate.py` | CLI that computes metrics from a predictions file |
| `tests/test_metrics.py` | Unit tests with synthetic arrays only |

## Prediction format

```json
[
  {
    "claim_id": "3",
    "predicted_label": "SUPPORTED",
    "retrieved_doc_ids": [14717500],
    "latency_ms": 812.5
  }
]
```

JSONL is also accepted. `predicted_label` must be one of `SUPPORTED`,
`CONTRADICTED`, `INSUFFICIENT_EVIDENCE` (case-insensitive). `VERIFICATION_ERROR`
records should be excluded or reported separately.

## Run

```bash
# 1. Download SciFact separately (license acceptance required), e.g.:
#    https://github.com/allenai/scifact
# 2. Export claims_test.jsonl in the official format.
# 3. Produce predictions through the AEGIS pipeline (adapter not yet implemented).
python experiments/evaluate.py \
  --claims data/scifact/claims_test.jsonl \
  --predictions experiments/predictions/scifact_test_predictions.json \
  --output experiments/results/scifact_test_metrics.json
```

The script exits with an error and writes nothing if inputs are missing. It never
invents or caches scores.

## Current gap

The SciFact → AEGIS corpus adapter (building a Db2 evidence document per abstract and
mapping `cited_doc_ids` to `document_id`) is not implemented. Until it exists, there
are no legitimate AEGIS predictions to score. This is deliberate: no benchmark claim
without an executed run.

## Separation from the demo

`data/samples/` contains a fictional SolarCell-X demonstration. Its output is not
SciFact performance and must never be presented as such.
