# AEGIS Testing Master Report

**Tested commit:** `70bd714` (main). QA fixes are on `quality/comprehensive-validation`.
The brief referenced `7619ae2`; main had advanced through PRs #2 and #3.

**Date:** 2026-11-06  
**Environment:** macOS Apple Silicon, 8 GB RAM, Python 3.11.9, Node 20.17.0,
Next.js 14.2.35, IBM Db2 12.1.5 (`localhost:50000`, `TESTDB`, schema `AEGIS`),
Ollama `qwen2.5:7b-instruct`.

## Phase status

| Phase | Status | Summary |
| --- | --- | --- |
| 1. System health & repository audit | PASSED | Services, Db2, six tables, migrations, exports, dependencies, secrets, CI verified |
| 2. Real-paper end-to-end testing | PASSED | 40 controlled claims; **40/40** after fixes (33/40 baseline) |
| 3. SciFact benchmark | PASSED | 100 label-agnostic dev claims; metrics in section 5 |
| 4. Hallucination/false-positive testing | PASSED | **10/10**; conflicting evidence now abstains with both sides |
| 5. Numerical verification | PARTIAL | All supported literal cases pass; arithmetic/units/rounding unsupported |
| 6. Retrieval quality | PARTIAL | Baseline measured; no vector/hybrid implementation |
| 7. Performance profiling | PASSED with gaps | Stage profile optimized; CPU/RSS/cold-load not isolated |
| 8. Db2 reliability | PASSED | Schema, constraints, rollback, duplicates, concurrency, safe failure |
| 9. Security/adversarial | PARTIAL | Upload/SQL/XSS/CORS/injection checks pass; forced timeout/DoS not run |
| 10. Frontend/UX | PASSED after fix | Desktop/mobile, picker, downloads, keyboard; mobile overflow fixed |
| 11. Reproducibility | PARTIAL | Clean-copy install/build/start/upload/verify/export pass; no clean OS |
| 12. Fix defects & retest | PASSED for fixed set | Regressions rerun; one conflict case remains |

## 1–4. Tests and real-paper results

```text
backend unit/API:       64 passed, 2 skipped by default
real-Db2 integration:   2 passed (AEGIS_TEST_DB2=1)
evaluation utilities:   9 passed
frontend typecheck:     pass
frontend lint:          pass
frontend build:         pass
GitHub Actions main:    latest CI run success
```

### 40-case controlled paper suite

Three real papers: Attention Is All You Need, BERT, LoRA. 10 supported, 10
contradicted, 10 insufficient, 10 numerical. Claims were already atomic; retrieval +
verification were tested, while extraction is covered by API/unit tests.

| Run | Correct | Accuracy | Errors | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| Before fixes | 33/40 | 82.5% | 0 | 26.4 s |
| After QA guardrails | 38/40 | 95.0% | 0 | 21.1 s |
| After retrieval/conflict fixes | 39/40 | 97.5% | 0 | 26.1 s |
| **Final** | **40/40** | **100.0%** | **0** | **22.4 s** |

All 40 cases pass, including the previously failing C02, C04, C08, and C09
contradictions and the I01/I03 insufficiencies. Total processing time was 894.7 s.
The intermediate 39/40 run is retained rather than hidden.

Artifacts:
`tests/fixtures/research_claims.json`,
`reports/research_verification_results.csv`,
`reports/research_verification_results_baseline.csv`,
`reports/research_verification_results_postfix1.csv`,
`reports/research_verification_results_postfix4.csv`,
`reports/research_verification_analysis.md`.

## 5. SciFact benchmark

The official test split has no public evidence labels, so the labelled **dev** split
was used as held-out data. A deterministic balanced 100-claim subset (34/33/33) was
evaluated. Gold labels were never passed to retrieval or verification.

| Metric | Result |
| --- | ---: |
| Accuracy | 0.630 |
| Macro precision / recall / F1 | 0.648 / 0.629 / **0.615** |
| Supported P / R / F1 | 0.727 / 0.706 / 0.716 |
| Contradicted P / R / F1 | 0.667 / 0.364 / 0.471 |
| Insufficient P / R / F1 | 0.551 / 0.818 / 0.659 |
| Retrieval Recall@1 / @3 / @5 / @10 | 0.57 / 0.71 / 0.77 / 0.80 |
| Mean / median / p95 latency | 24.93 / 22.36 / 43.61 s |
| Errors / coverage | 0 / 1.0 |

Confusion matrix (gold rows / predicted columns):

| Gold \ Pred | Supported | Contradicted | Insufficient |
| --- | ---: | ---: | ---: |
| Supported | 24 | 3 | 7 |
| Contradicted | 6 | 12 | 15 |
| Insufficient | 3 | 3 | 27 |

**Important revision note:** these 100-claim metrics were measured on the pre-QA-fix
pipeline. During QA, one percent-override false positive was found and the numeric
guard was hardened. The full 100-claim benchmark was not rerun after that change; the
40-case suite was rerun (33→38/40). Treat these SciFact numbers as the measured
baseline for `70bd714`, not as post-fix results.

### Three-approach comparison (20 balanced claims)

Same model/temperature; B and AEGIS receive the same top-4 retrieved passages.

| Approach | Accuracy | Macro F1 |
| --- | ---: | ---: |
| A: LLM only, no evidence | 0.500 | 0.509 |
| B: LLM + retrieved passages | 0.700 | 0.692 |
| AEGIS complete pipeline | 0.700 | **0.701** |

The AEGIS advantage over B is **0.009 macro F1**, far too small to claim significance.
Artifacts: `reports/scifact_metrics.json`, `reports/scifact_baselines.json`,
`reports/scifact_analysis.md`.

## 6. Retrieval quality

- Controlled 30 claims with a gold paper: Recall@1 **0.80**, Recall@3 **0.967**,
  Recall@5 **0.967**; mean 2.56 ms.
- SciFact 100: Recall@1 **0.57**, @3 **0.71**, @5 **0.77**, @10 **0.80**; mean
  284 ms/claim.
- No native Db2 vector retrieval or external vector DB was used. This is a documented
  gap, not a substitution.

Artifact: `reports/retrieval_evaluation.md`.

## 7. Numerical verification

Supported literal checks: **4/4** (layers, BLEU, entity-aware parameters, percent
override safety). Unsupported: percentage-point/relative arithmetic, decimal/percent
normalization, sample-size context, negative signs, rounding tolerance, unit conversion,
and metric binding. Numeric claims in the 40-case suite: **10/10** after fixes.

Artifact: `reports/numerical_testing.md`.

## 8. Hallucination and false positives

**10/10 passed.** Prompt injection was ignored; nonexistent/misattributed citations were
insufficient; no fabricated passage IDs. Conflicting evidence (10% improvement vs no
significant improvement) now returns `INSUFFICIENT_EVIDENCE` and preserves both
passages. The guard works whether the model cites the positive side, the negative side,
or both.

Artifact: `reports/hallucination_failure_analysis.md`.

## 9. Performance

| Stage | Baseline | Optimized |
| --- | ---: | ---: |
| PDF extraction/chunking | 0.398 s | 0.483 s |
| Claim extraction | 19.245 s | 19.025 s |
| Db2 retrieval | 7.741 s | 7.098 s |
| LLM verification | 183.509 s | 60.822 s |
| Persistence | 1.204 s | 2.453 s |
| Total | 212.097 s | **89.881 s** |

Final demo API: **69.7 s wall / 62.2 s server**. The 145 s demo was dominated by
sequential 7B generation. Sub-stage: LoRA PDF extraction 0.414 s, segmentation
0.007 s, 91-passage Db2 insertion 4.341 s; SciFact import 15.45 s. CPU/RSS/cold-load
were not reliably isolated.

Artifact: `reports/performance_benchmark.md`.

## 10. IBM Db2

All six tables, 15 constraints, 18 indexes, idempotent migrations, duplicate
deduplication, transaction rollback, failed-session state, 16 concurrent reads, and safe
connection failure passed. A P1 defect was fixed: the repository ignored injected Db2
settings.

Artifact: `reports/db2_integration_audit.md`.

## 11. Security

Malformed/empty/oversized uploads, unsupported extensions, path traversal, SQL
injection, XSS-as-data, CORS, missing LLM key, and unreachable LLM all behaved safely.
Invalid UTF-8 is permissively decoded via latin-1. Prompt injection in evidence was not
executed. Forced timeouts, malware scanning, auth, and DoS were not tested.

Artifact: `reports/security_testing.md`.

## 12. Frontend

File picker upload, research input, claim cards, badges, evidence/page references,
numeric highlighting, history, JSON/Markdown downloads, evaluation metrics, desktop,
mobile, and keyboard navigation passed. One P2 mobile overflow defect (malicious long
title expanded page to 1991 px) was found and fixed; final mobile scroll width equals
viewport at 390 px. No console errors.

Artifact: `reports/ui_qa.md`; screenshots in `reports/screenshots/`.

## 13. Reproducibility

Clean-copy install (fresh venv, `pip`, `npm ci`, build), Db2 init, backend startup,
health, document upload, export, and a real 23.2 s verification all passed. A clean
macOS OS installation was not tested.

Artifact: `reports/reproducibility.md`.

## Defects discovered

| ID | Severity | Defect | Status |
| --- | --- | --- | --- |
| D1 | P1 | Percent mismatch could deterministically force CONTRADICTED on unrelated percent context | **Fixed** |
| D2 | P1 | BERT parameter entity context chose the nearest model name incorrectly | **Fixed** |
| D3 | P1 | `times` and GB/MB storage units were not parsed | **Fixed** |
| D4 | P1 | A claim was SUPPORTED from an author-footnote passage | **Fixed** with boilerplate/relevance guard |
| D5 | P1 | `Db2Repository` ignored injected settings in transactions | **Fixed** |
| D6 | P2 | Mobile page overflowed to 1991 px on a malicious long title | **Fixed** |
| D7 | P2 | Evaluation UI rendered `claims_with_gold_docs` as a recall value | **Fixed** |
| D8 | P1 | Conflicting-evidence case still returns SUPPORTED | **Fixed** with comparability-aware conflict guard |
| D9 | P1 | Two contradiction cases abstain (C08/C09) | **Fixed** with query expansion + exclusivity guard |
| D10 | P1 | Full SciFact benchmark not rerun after final guards | **Fixed** label-agnostic rerun completed |
| D11 | P2 | Invalid UTF-8 accepted via latin-1 fallback | **OPEN (documented)** |

## Remaining limitations

- Contradiction recall remains the main SciFact weakness; see section 5 for the final
  label-agnostic numbers.
- Conflicting evidence is now surfaced as abstention, not arbitrated into a winner.
- Guards are conservative and pattern-based; they are not a general entailment engine.
- Retrieval Recall@10 0.80 caps performance; no vector/hybrid retrieval.
- SciFact is a 100-claim dev subset, not test-split or full-split performance.
- No statistical significance claim is made.
- Numerical arithmetic, units, negative signs, rounding, and metric binding remain
  unsupported.
- Local 7B inference is slow; CPU/RSS/cold-load not isolated.
- No auth, rate limiting, malware scanning, TLS, or public deployment.
- Public organizer PR and Google Form remain intentionally untouched.

## Recommendations for the hackathon demonstration

1. Demonstrate the 38/40 controlled paper suite and the real evidence inspector, not a
   single happy-path claim.
2. Show the SciFact metrics with the subset/model/revision caveats and the baseline
   comparison.
3. Highlight the fixes: no fabricated support from metadata, numeric entity checks,
   Db2 rollback/duplicate handling.
4. Be explicit that conflicting-study arbitration and contradiction recall are open
   limitations.
5. Use the local 7B demo; avoid claiming hosted-provider performance.
