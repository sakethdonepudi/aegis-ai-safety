# AEGIS Demonstration

## What the demo is

A small, **clearly labelled synthetic** study about a fictional technology,
"SolarCell-X". All numbers are fictional. The demo exists to exercise the real
pipeline: claim extraction → Db2 retrieval → LangChain assessment → evidence
validation → Db2 persistence → dashboard rendering.

No classification is hardcoded. The same workflow accepts any new research text and
evidence.

## Demo inputs

Research text (`data/samples/synthetic_research_text.txt` or the **Load demo** button):

1. SolarCell-X achieved a conversion efficiency of 92% under standard test conditions.
2. The dual-layer anti-reflective coating reduced manufacturing cost by 40% compared
   with the baseline production process.
3. SolarCell-X cells retained 95% of their initial efficiency after five years of outdoor
   operation.

Evidence (`data/samples/synthetic_solarcell_study.txt`):

- The trial reports **92%** conversion efficiency under standard test conditions.
- The coating reduced manufacturing cost by **15%**, not 40%.
- The trial did **not evaluate** outdoor conditions and performed **no long-term
  degradation testing**, so the five-year retention claim is unsupported.

The three statements are designed to exercise the three substantive outcomes:

- Claim 1 has an explicit supporting passage → expected `SUPPORTED`.
- Claim 2 conflicts with the stated 15% → expected `CONTRADICTED`.
- Claim 3 is not established by the evidence; the absence of long-term testing is not
  proof that the retention figure is false → expected `INSUFFICIENT_EVIDENCE`.

These are the intended outcomes, not hardcoded results. The configured model may make
a different judgment, and AEGIS records what actually happened along with limitations.

## Run it

```bash
cp .env.example .env
# configure DB2_* and LLM_*
make db-init
make db-seed
make dev-backend      # terminal 1
make dev-frontend     # terminal 2
```

Open `http://localhost:3000` and click **Load demo**, then **Verify research claims**.

The demo uses pasted evidence, so it works even if `db-seed` was not run. The seeded
document is useful for the evidence library and history view.

## API-only demo

```bash
python3 - <<'PY'
import json, pathlib
text = pathlib.Path("data/samples/synthetic_research_text.txt").read_text()
evidence = pathlib.Path("data/samples/synthetic_solarcell_study.txt").read_text()
print(json.dumps({"submitted_text": text, "document_ids": [], "evidence_text": evidence,
                  "evidence_title": "Synthetic demo — SolarCell-X trial (fictional)"}))
PY
```

Send the resulting JSON:

```bash
curl -s -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d @payload.json | python3 -m json.tool
```

## What to look for in the UI

- **Overview:** total claims and the distribution across supported, contradicted,
  insufficient evidence, and errors.
- **Claim inspector:** each atomic claim with its classification.
- **Evidence viewer:** the exact retrieved passage, document title, page and passage
  reference, retrieval score, explanation, limitations, and verification method.
- **No evidence link:** an insufficient-evidence claim explains that missing evidence
  is not contradiction.
- **History:** reopen the same session; data comes from Db2, not browser state.

## Verified local result

On 2026-11-05 the demo was executed through the real UI → FastAPI → LangChain →
Db2 path using `qwen2.5:7b-instruct` served by Ollama (temperature 0). The synthetic
session produced:

| Claim | Classification | Evidence |
| --- | --- | --- |
| SolarCell-X achieved 92% efficiency under standard test conditions | `SUPPORTED` | Passage 61, page 1 |
| The coating reduced manufacturing cost by 40% | `CONTRADICTED` | Passage 61 (source says 15%) |
| Cells retained 95% efficiency after five years outdoors | `INSUFFICIENT_EVIDENCE` | 2 retrieved passages; none establish it |

The session (3 claims, 1/1/1) was persisted in Db2 and reopened from the history panel.
A real-model run takes roughly 30–100 seconds for three claims on a local 7B model.
This is a **synthetic demonstration, not a SciFact benchmark result**.

Synthetic demo output is never presented as SciFact benchmark performance.
