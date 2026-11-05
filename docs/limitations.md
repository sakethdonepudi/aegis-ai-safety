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
- **No numeric or unit reasoning engine.** Numbers are preserved and compared by the
  model; unit conversion, statistical significance, and table parsing are not
  implemented.
- **No citation verification.** AEGIS verifies claims against supplied evidence, not
  whether a paper's external citations exist or say what is claimed.
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
- Request timeout is 300 seconds; long multi-claim documents can hit it.
- Sessions are never deleted by the application; retention is a database operation.

## Evaluation

- SciFact is **not** bundled and is licensed CC BY-NC 2.0 (non-commercial).
- The harness supports macro F1, per-class precision/recall, confusion matrix,
  false-positive analysis, retrieval Recall@K, and latency statistics.
- **No benchmark has been executed.** No F1, accuracy, or latency number in this
  repository should be read as a benchmark result.
- Synthetic demo outcomes are not benchmark evidence.
- SciFact labels are SUPPORT / CONTRADICT / NEI, mapped to AEGIS's three substantive
  classes. `VERIFICATION_ERROR` is operational, not a gold label.

## Scope

- Not a general-purpose chatbot.
- Not a plagiarism detector, peer reviewer, or scientific truth oracle.
- Only judgments with validated evidence links can be `SUPPORTED` or `CONTRADICTED`;
  a model response that cites an unknown passage is downgraded.
- Missing evidence is never classified as contradiction.
