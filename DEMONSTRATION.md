# Demonstration

> AI-assisted evidence draft. Independently student-written wording and the
> owner's personal assessment remain pending.

## Actual method

The doing agent was Codex Work using `mcp/client.py`, an explicit configured
stdio client. It inspected the server's actual catalog, chose two queries on
the owner's actual workbook and produced summaries from the results. This is
not native Codex MCP registration or a browser WebMCP call.

Two separate fresh-context agents each reviewed one task using the checker,
task criteria, saved calls and relevant source. They did not receive the doing
conversation, expected verdicts or the other run. Both independently repeated
their read-only query and compared original-workbook hashes. No different-model
claim is made.

Private argument values, returned records, row IDs, dates, file paths and source
fingerprints have been removed from the public fragments below. Redaction
markers are not literal arguments sent to the server. The private originals
are retained locally; the public count/truncation fields and review outcomes
are unchanged.

## Run 1 — Organization application summary

Task: summarize one organization's applications while excluding another company
that coincidentally matches its name as a substring.

Actual wire fragment with private values redacted:

```json
{"method":"tools/call","params":{"name":"application_tracker","arguments":{"action":"query","company":"[REDACTED]","limit":100}}}
```

The response had `isError:false`, `total:3`, `truncated:false`. Two records
belonged to the intended organization; the third was a different company and was
excluded from the summary count. The doing agent preserved original fields
privately and described statuses as tracker records, not new employer decisions.

Fresh reviewer outcome: all six task criteria MET, no priority gaps. It compared
the exact reported fields against the original response, repeated the real
query and independently confirmed unchanged before/after source hashes. It
also passed the seven then-existing synthetic tests.

## Run 2 — Pending data-role review

Task: identify records satisfying both a role-title substring and a recorded
status substring, preserving source spelling and limiting the scope claim.

```json
{"method":"tools/call","params":{"name":"application_tracker","arguments":{"action":"query","title":"[REDACTED]","status_filter":"[REDACTED]","limit":100}}}
```

The actual response had `isError:false`, `total:4`, `truncated:false`. The agent
included all four matches, retained company spelling privately and explained
that roles outside the title filter were outside this selection. It did not
invent hiring outcomes, submit anything or contact anyone.

Fresh reviewer outcome: all six task criteria MET, no priority gaps. It repeated
the query and independently corroborated the exact four records and unchanged
source hashes. Two relevant existing synthetic tests passed.

Neither real-task call updated the original workbook. Update tests used copies.
Historical execution was assessed from captured evidence and corroborated with
fresh calls; reviewers did not independently witness the original timestamps.

## Separate component and skill checks

A fresh agent selected the trivial ping from custom-client metadata, loaded it
through the client and returned exactly `HW8-SKILL-PING: LOADED`. A later fresh
agent selected/loaded acceptance-check the same way and reviewed the entire MCP
component: eight criteria MET, eight tests passed, and a real-workbook-copy wire
query/update/requery preserved original bytes. Native automatic skill discovery
remains unconfirmed; the late probe does not retroactively satisfy setup order.

A separate review also caught a preservation bug after the original seven
tests passed. [ITERATION.md](ITERATION.md) records the genuine failing cases and
fix; passing read-only summaries did not prove updates correct.

**Owner's assessment: pending.** The owner still needs to explain their own
agreement or disagreement with the checker. AI findings cannot supply that
personal judgment or an independently student-written narrative.
