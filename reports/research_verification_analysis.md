# Real-Paper Verification Analysis

## Test set

40 controlled claims over three real arXiv papers:

- *Attention Is All You Need* (arXiv 1706.03762)
- *BERT* (arXiv 1810.04805)
- *LoRA* (arXiv 2106.09685)

The PDFs were parsed with PyMuPDF, stored in IBM Db2 with page provenance, and used as
the evidence corpus. Fixture: `tests/fixtures/research_claims.json`.

| Category | Cases |
| --- | ---: |
| Supported | 10 |
| Contradicted | 10 |
| Insufficient evidence | 10 |
| Numerical (supported and contradicted) | 10 |
| **Total** | **40** |

Claims are already atomic in the fixture, so this suite isolates retrieval, evidence
grounding, numeric checks, and attribution. Claim extraction is tested separately by the
application and API tests. Expected labels are stored only for scoring.

## Results

| Run | Correct | Accuracy | Errors |
| --- | ---: | ---: | ---: |
| Baseline (before fixes) | 33/40 | 82.5% | 0 |
| **After fixes** | **38/40** | **95.0%** | **0** |

Post-fix category results:

| Category | Correct | Accuracy |
| --- | ---: | ---: |
| Supported | 10/10 | 100% |
| Contradicted | 8/10 | 80% |
| Insufficient | 10/10 | 100% |
| Numerical | 10/10 | 100% |

Mean processing time: **21.07 s/claim**, total **842.7 s** for 40 cases. Model:
`qwen2.5:7b-instruct`, temperature 0.

## Remaining failures

Both are contradiction cases where the model abstained instead of contradicting:

- **C08:** “BERT must be trained from scratch for every downstream task.” → predicted
  `INSUFFICIENT_EVIDENCE`; the model did not cite a passage.
- **C09:** “LoRA stores a complete fine-tuned model copy for every task.” → predicted
  `INSUFFICIENT_EVIDENCE`; the model did not cite a passage.

The retriever/model did not connect these negations to the source statements about
fine-tuning and LoRA weight swapping. This is a missed-contradiction (false-abstention)
problem, not a false-support problem.

## Fixes validated by the suite

1. **Boilerplate/irrelevant-passage false support (I07):** a claim about protein folding
   was previously `SUPPORTED` from an author-footnote passage. The new boilerplate +
   overlap guard downgrades it to `INSUFFICIENT_EVIDENCE`.
2. **Numerical entity matching (N07):** BERT-base 340M is now contradicted using
   BERTBASE 110M, instead of matching BERTLARGE 340M.
3. **Times/storage-size units (N09/N10):** 10× vs 3× and 35GB vs 35MB are now caught.
4. **Percent override safety:** percent mismatches no longer deterministically override
   the model; the SciFact false CONTRADICTED case was addressed.
5. **S02:** “based solely on attention” is now SUPPORTED after the improved prompt.

## Artifacts

- Baseline CSV: `reports/research_verification_results_baseline.csv`
- Post-fix CSV: `reports/research_verification_results.csv`
- Post-fix summary: `reports/research_verification_summary.json`

## Interpretation

The controlled suite is not a representative scientific benchmark and is not used to
claim general accuracy. It demonstrates:

- strong handling of explicit support and insufficient evidence;
- improved numerical and attribution behavior after fixes;
- a remaining weakness on negated/contrastive claims requiring multiple passages.

The two missed contradictions are visible in the evidence inspector and are documented
as a P1 limitation rather than hidden.
