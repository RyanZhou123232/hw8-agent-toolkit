# Homework 8 — Agent Toolkit

> AI-assisted draft requested by the owner. Independently student-written prose
> and the owner's personal assessment remain pending.

This toolkit pairs a report-only acceptance checker with one local MCP tool,
`application_tracker`. The skill reviews work against criteria, names conflicts
and cites evidence. The tool queries an existing Excel tracker and can update
only status/notes, with current-version checks and exact backups.

## Motivation from earlier work

The owner's [HW7 Phase 2 Prompt 2](https://github.com/RyanZhou123232/chaos-lab-phase2/blob/main/prompt_log.md)
says:

> 它的这个不一致你把它记录下来。
> 你就它怎么验收你就怎么写。

[Naevia prompt 7](https://github.com/RyanZhou123232/Naevia/blob/main/prompt_log.md)
repeats the emphasis on checking an explicit standard:

> 这个要求你看看现在的spec满不满足

These owner prompts motivated conflict handling and evidence-based review.
They are not the inherited HW7 Phase 1 author's prompts.

The [HW6 actual-pipeline walkthrough](https://github.com/RyanZhou123232/vector-memory/blob/main/prompt_log.md)
asks to inspect exactly which structured records were returned:

> 每个检索句我们的这个 database 具体返回了哪四十条 line

The application workbook is a different existing source selected during HW8.
The MCP adapter exposes its rows/filters/versions rather than reconstructing
records from chat. This is evidence for structured access, not a claim that an
application-specific MCP was requested in HW6. Not every HW3–HW7 log was available.

## Install

Python 3.10+; server/client/test suite use only the standard library:

```powershell
python -m venv --without-pip .venv
.venv/Scripts/python.exe -B -m unittest discover -s mcp -v
```

Copy `skills/acceptance-check/` into `.agents/skills/acceptance-check/` in the
project you want to review. The existing `.agents/skills/hw8-skill-ping/` is a
visible loading probe. Confirm discovery in your own client; folder placement
alone proves no loading.

For native Codex MCP registration, merge this into the existing
`~/.codex/config.toml`, preserving other settings. All `C:/YOUR_...` paths are
placeholders to replace on your machine:

```toml
[mcp_servers.application_tracker]
command = 'C:/YOUR_PROJECT/.venv/Scripts/python.exe'
args = ['C:/YOUR_PROJECT/mcp/server.py']
[mcp_servers.application_tracker.env]
APPLICATION_TRACKER_PATH = 'C:/YOUR_DATA/applications.xlsx'
APPLICATION_TRACKER_SHEET = 'Sheet1'
```

A separate VS Code Copilot example is in `.vscode/mcp.json`.
[mcp/SETUP.md](mcp/SETUP.md) documents the workbook contract and explicit client.

## Confirmed client path

Native Codex performed a local server handshake/discovery, but native model
startup failed in the network-restricted execution environment. The working
demonstrations used Codex Work with an explicit JSON-configured stdio CLI client.
It is not native Codex MCP registration.

Copy `mcp/client-config.example.json` to a private local config and replace its
placeholder paths. Configure `skills_directories` for metadata discovery:

```powershell
python mcp/client.py --config PRIVATE_CONFIG.json skills
python mcp/client.py --config PRIVATE_CONFIG.json skill acceptance-check
python mcp/client.py --config PRIVATE_CONFIG.json list
'{"action":"query","company":"Example Co","limit":100}' | python mcp/client.py --config PRIVATE_CONFIG.json call application_tracker
```

The Example Co query is illustrative; it is not a real demonstration result.
The agent discovers the real catalog, selects call arguments and uses returned
records. A fresh independent checker then reviews each result.

## Verification

| Check | Observed result |
| --- | --- |
| Server suite | Eight tests pass, including neighboring-cell byte preservation |
| Real-workbook copy | Actual MCP query/update/requery, exact backup and independent readback pass; original unchanged |
| Two real tasks | Explicit CLI MCP calls followed by separate fresh-context checker reviews |
| Custom-client skill discovery | Fresh agent selected the ping from metadata and returned its visible marker |
| Native automatic skill loading / VS Code UI | Unconfirmed |

[DEMONSTRATION.md](DEMONSTRATION.md) contains redacted real-run evidence;
[ITERATION.md](ITERATION.md) describes a genuine false-pass checker review and
the subsequently discovered data-preservation defect. Private records, local
configuration and full personal transcripts are not published.

Filters are case-insensitive substrings combined with AND. Resolve the intended
company/job before updating. Notes replace notes. Test writes on copies; the
cooperative lock does not coordinate unrelated writers. Excel is the only data store.

## Sources and AI assistance

The checker adapts the course's [spec-check example](https://www.cs.cmu.edu/~113/hw8.html),
adding precedence, compound criteria, verification limits, scratch-output rules
and direct evidence for preservation claims. Protocol references:
[stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports),
[initialization](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle),
[tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools).
Native configuration references: [Codex skills](https://developers.openai.com/codex/skills)
and [Codex MCP](https://developers.openai.com/codex/mcp).
The tools-only protocol subset is implemented directly after SDK installation
was blocked; broad client certification is not claimed.

AI assisted with code, tests, troubleshooting, these drafts and independent
reviews. Reviewers started without doing-agent conversation or expected answers;
no different-model claim is made. The owner's agreement with a checker is not
generated or asserted here.
