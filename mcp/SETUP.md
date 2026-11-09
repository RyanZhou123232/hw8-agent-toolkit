# Application tracker setup

Python 3.10+, standard library only. The server is local stdio and exposes only
`application_tracker`, with query/update actions. It does not read email, submit
applications or send messages. It uses the configured workbook as its sole store.

## Workbook contract

Configure an `.xlsx` workbook and sheet using environment variables
`APPLICATION_TRACKER_PATH` and `APPLICATION_TRACKER_SHEET` (default Sheet1).
The sheet must have these exact row-5 headers:

| Cell | Header |
| --- | --- |
| D5 | Company |
| E5 | link |
| F5 | Title |
| G5 | App day |
| L5 | status |
| M5 | other info |

Application rows start at row 6. Q can provide an application link. Formulas in
read data cells and protected worksheets are rejected. The account workbook
filename named in tracker.py is rejected as outside scope; caller paths are never accepted.

## Native clients

Create `.venv` as shown in README, then replace every placeholder in the README
Codex TOML example or `.vscode/mcp.json`. Paths are machine-specific. Preserve
unrelated client settings. Restart/reload the client's configured server and
inspect the real tool catalog and tool call; starting Python alone proves no
agent invocation. Native VS Code UI and native Codex model calls were not
confirmed in this environment.

## Explicit CLI adapter used in the real runs

Copy `client-config.example.json` to an ignored private file, replace its command,
args and environment paths, and point `skills_directories` to the desired local
skill folders. The client reads this project's single-line name/description
frontmatter; it is not a full YAML implementation.

```powershell
python mcp/client.py --config PRIVATE_CONFIG.json skills
python mcp/client.py --config PRIVATE_CONFIG.json skill acceptance-check
python mcp/client.py --config PRIVATE_CONFIG.json list
'{"action":"query","company":"Example Co","limit":20}' | python mcp/client.py --config PRIVATE_CONFIG.json call application_tracker
```

The illustrative company is synthetic. The client actually launches the
registered server and sends initialize, initialized notification, tools/list
and tools/call. It is an explicit adapter invoked by the agent, not a native
Codex registration. Skill discovery through it is also distinct from native
automatic loading. Optional `--evidence PATH` saves a projection omitting query
links/notes; inspect other returned fields before any public sharing.

## Operations and boundaries

Query filters are case-insensitive company/title/status substrings combined
with AND. Limit is 1–100; total and truncated expose omitted records. Updates
require a row and matching current version obtained from a query. Only new_status
and new_notes are accepted; empty notes clears notes, unspecified fields remain.
Notes replace existing notes. Never invent application outcomes.

Updates create an exact backup beside the configured file, then replace it.
Formula-looking input remains literal text. Close Excel before writes; its
ownership marker, a cooperative MCP lock or a stale version blocks an update.
The lock does not coordinate unrelated writers. Serialize writes with other
workflows. Backups contain the same private data as the source.

Test mutations on disposable copies. The eight synthetic tests exercise real
subprocess MCP and preserve non-target bytes, including absent/self-closing
cells. An independent review also verified a real-workbook copy; original bytes
were unchanged. Native UI/model invocation is a separate unconfirmed path.

The direct tools-only implementation supports protocol versions 2024-11-05,
2025-03-26 and 2025-06-18; other requested versions negotiate 2025-06-18.
Protocol references are linked in README. No full MCP feature/client certification
is claimed.
