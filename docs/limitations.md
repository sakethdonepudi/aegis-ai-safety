# Limitations and Known Issues

AEGIS is an initial research application. It is not a guarantee of factual accuracy
and not a production-hardened service.

## Verification quality

- **LLM dependence.** Claim extraction and judgments depend on the configured model.
  Smaller or local models may produce malformed JSON, weak reasoning, or incorrect
  classifications. Every result remains subject to researcher review.
- **Prompts are not proofs.** A supported/contradicted label reflects the model's
  reading of retrieved passages, not a formal entailment proof.
- **One passage set per claim.** Retrieval can miss relevant evidence that uses
  different vocabulary. This produces `INSUFFICIENT_EVIDENCE`, not contradiction.
- **Narrow numeric checker.** The deterministic verifier covers only simple literal
  expressions (percentages, BLEU, parameter/layer/head/GPU/day/word counts). It does not
  parse tables, equations, units, confidence intervals, p-values, or advanced
  statistics. A clear literal conflict can override an inconsistent model judgment, but
  entity ambiguity can still cause mistakes.
- No citation-existence verification (Crossref/DOI lookup is future P1 work). AEGIS
  verifies claims against supplied evidence, not whether external citations exist.
- **English-centric prompts and tokenizer.** Other languages are not evaluated.

## Retrieval

- Lexical BM25 over Db2-stored passages only. There is no vector search, reranker, or
  cross-encoder in this version.
- The SQL prefilter uses `LIKE` with up to 12 claim tokens; a very large passage table
  would need a better index or native full-text/vector retrieval.
- Candidate cap is 500 passages per claim; top K defaults to 6.
- Embedding similarity is explicitly not treated as factual support.

## Documents

- Text-based PDFs only. Scanned/image PDFs require OCR, which is not implemented.
- Encrypted PDFs are rejected.
- Upload limit is 10 MB; submitted/pasted text is capped at 30,000 characters.
- Raw uploaded files are not retained; only extracted passages and metadata are stored.
- No document deletion, versioning, or per-document permissions.
- PDF page text is chunked by sentence heuristics; complex layouts, tables, equations,
  and figures are not reconstructed.

## Platform and operations

- **ibm_db parameter-marker bug.** On macOS Apple Silicon with `ibm_db` 3.3.0,
  `exec_immediate` with parameters can segfault. AEGIS uses prepared statements
  (`prepare` + `bind_param` + `execute`) and frees them; SQL remains parameterized.
  Db2 statement handles are freed explicitly to avoid process-exit crashes.
- Db2 Community Edition 12.1.5 container images are `linux/amd64`; Apple Silicon runs
  them under emulation, which is slow to initialize and can exhaust 8 GB machines.
- No authentication, authorization, multi-tenancy, quotas, or rate limiting.
- No background jobs: verification is synchronous and may take tens of seconds.
- No streaming progress; the UI shows a spinner until completion.
- No automated browser E2E suite or accessibility audit. Frontend build, typecheck,
  and backend tests are automated.
- No TLS termination, WAF, or secrets manager in local development.
- Logs avoid document content, but request metadata and errors are logged at INFO/WARN.
- CORS is explicit; production origins must be configured.
- Hosted deployment requires a hosted Db2 with private networking. A local Db2 cannot
  back a public backend.
- Request timeout is 600 seconds by default; local 7B inference can take minutes for
  four claims, and long documents can still hit the bound.
- Reports (JSON/Markdown) and history have no authentication or access control. They are
  intended for a local single-user deployment.
- The paper demo downloads arXiv PDFs at setup time and does not commit them; offline
  users must use the synthetic demo or supply their own PDFs.
- Sessions are never deleted by the application; retention is a database operation.

## Evaluation

- SciFact is **not** bundled and is licensed CC BY-NC 2.0 (non-commercial).
- The harness supports macro F1, per-class precision/recall, confusion matrix,
  false-positive analysis, retrieval Recall@K, and latency statistics.
- The measured run used a **balanced 100-claim subset of the 300 labelled dev claims**
  (34 supported / 33 contradicted / 33 insufficient), not the full split and not the
  hidden-label test split. Macro F1 was 0.615 and retrieval Recall@10 was 0.80 with
  local `qwen2.5:7b-instruct`.
- Contradiction recall (0.364) is the main weakness; 15 of 33 contradicted claims were
  classified as insufficient evidence. Retrieval Recall@10 (0.80) bounds classification
  performance.
- This is a single-model, single-run result. Do not claim statistical significance or
  general superiority from it.
- The Evaluation section shows measured results only when a real metrics file exists;
  otherwise it shows an explicit empty state.
- Synthetic/paper demo outcomes are not benchmark evidence.
- SciFact labels are SUPPORT / CONTRADICT / NEI, mapped to AEGIS's three substantive
  classes. `VERIFICATION_ERROR` is operational, not a gold label.

## Scope

- Not a general-purpose chatbot.
- Not a plagiarism detector, peer reviewer, or scientific truth oracle.
- Only judgments with validated evidence links can be `SUPPORTED` or `CONTRADICTED`;
  a model response that cites an unknown passage is downgraded.
- Missing evidence is never classified as contradiction.
