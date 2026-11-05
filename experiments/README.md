# Experiments — SciFact Evaluation

Reproducible SciFact evaluation for AEGIS. The adapter, Db2 import, retrieval
evaluation, verifier predictions, and metrics are implemented. The latest measured run
is stored under `experiments/results/`.

## Dataset: SciFact

- **Source:** https://github.com/allenai/scifact and
  https://huggingface.co/datasets/allenai/scifact
- **Archive:** https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
- **License:** **CC BY-NC 2.0** (https://creativecommons.org/licenses/by-nc/2.0/).
  The dataset is not redistributed and must not be used commercially.
- **Corpus:** 5,183 abstracts.
- **Splits:** 1,261 train / 300 dev / 300 test claims in this release.
- **Evaluation split:** the official **test** split does not publish evidence labels,
  so the **dev** split (300 labelled claims) is used as the held-out labelled set.
  AEGIS never trains on SciFact.
- **Labels:** `SUPPORT` → `SUPPORTED`, `CONTRADICT` → `CONTRADICTED`, `NEI` →
  `INSUFFICIENT_EVIDENCE`.

Manifest: [`scifact_manifest.json`](scifact_manifest.json).

## Files

| File | Purpose |
| --- | --- |
| `scifact_loader.py` | Load corpus and claim JSONL/JSON; derive labels and cited docs |
| `scifact_adapter.py` | Convert abstracts into Db2 documents with external IDs |
| `retrieval_eval.py` | Full-corpus BM25 index loaded from Db2 |
| `run_scifact_eval.py` | Import, retrieve, verify, checkpoint predictions, compute metrics |
| `metrics.py` | Macro F1, per-class precision/recall, confusion matrix, FP analysis, Recall@K, latency |
| `benchmark.py` | Alias entry point for metrics from an existing predictions file |
| `evaluate.py` | Metrics CLI |
| `profile_pipeline.py` | Per-stage pipeline profiling |
| `tests/test_metrics.py` | Metric unit tests |

## Run the evaluation

```bash
make scifact-data          # downloads SciFact separately (license: CC BY-NC 2.0)
python experiments/run_scifact_eval.py --import --limit 100 --model qwen2.5:7b-instruct
```

The runner:

1. imports all 5,183 abstracts into Db2 (`source_type='scifact'`, external IDs preserved);
2. loads dataset passages from Db2 and builds a full-corpus BM25 index;
3. retrieves top-10 passages per claim without using gold labels;
4. passes only the claim and top 4 retrieved passages to the verifier;
5. writes predictions incrementally (resumable);
6. scores macro F1, per-class precision/recall, confusion matrix, false positives,
   retrieval Recall@1/5/10, and latency.

`--limit 0` evaluates all 300 labelled dev claims. A nonzero limit creates a
deterministic balanced subset and is reported explicitly; do not present subset results
as full-split results.

### Prediction format

JSONL records include:

```json
{"claim_id":"3","predicted_label":"SUPPORTED","retrieved_doc_ids":[123],
 "evidence_passage_ids":[45],"retrieval_ms":170.2,"verification_ms":41000,
 "latency_ms":41170.2,"numerical_analysis":null}
```

Gold labels are stored only in the evaluation split and are joined at scoring time;
they are never passed to retrieval or the verifier.

## Latest results

See [`results/scifact_dev_metrics.json`](results/scifact_dev_metrics.json) and
[`predictions/scifact_dev_predictions.jsonl`](predictions/scifact_dev_predictions.jsonl).
The report includes the model, subset size, coverage, errors, and settings.

## Performance

`python experiments/profile_pipeline.py` records PDF processing, claim extraction, Db2
retrieval, LLM verification, and persistence separately. See
[`docs/performance.md`](../docs/performance.md).

## Separation from the demo

`data/samples/` contains a fictional SolarCell-X demo and a synthetic paper-demo
summary. Those outcomes are not SciFact performance and must never be presented as
such.
