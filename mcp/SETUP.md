# Application tracker setup

Python 3.10+ is required. The server, explicit client and tests use only the
standard library; no pip packages are needed. Run the commands below from the
repository root, the directory containing README.md and mcp/.

## 1. Prepare the Python environment

```powershell
python -m venv --without-pip .venv
.\.venv\Scripts\python.exe -B -m unittest discover -s mcp -v
```

The current suite contains eight tests using disposable synthetic workbooks.
It starts the actual stdio server and checks queries, updates, errors, backups
and preservation of neighboring cells. It does not use your personal workbook.

These commands use Windows PowerShell. On macOS/Linux, use `.venv/bin/python`
in place of `.venv/Scripts/python.exe`.

## 2. Install the checker skill

Copy the complete `skills/acceptance-check/` folder into
`.agents/skills/acceptance-check/` in the project you want to review. Keep
`SKILL.md` inside that folder. For this repository, the resulting file is:

```text
.agents/skills/acceptance-check/SKILL.md
```

A trivial loading probe is already provided under
`.agents/skills/hw8-skill-ping/`. Ask your client to
perform the HW8 skill ping and inspect whether it actually loads the skill.
The expected response is `HW8-SKILL-PING: LOADED`. Folder placement alone does
not establish loading.

Use the checker in a separate fresh session from the agent that produced the
work. Supply the requirements file and the artifact/project to review.

## 3. Configure a compatible workbook

Use an existing `.xlsx` workbook. The selected sheet must have these exact
headers in row 5:

| Cell | Header |
| --- | --- |
| D5 | Company |
| E5 | link |
| F5 | Title |
| G5 | App day |
| L5 | status |
| M5 | other info |

Application rows start at row 6. Column Q optionally provides an application
link. Set `APPLICATION_TRACKER_PATH` to the workbook's absolute path and
`APPLICATION_TRACKER_SHEET` to its sheet name (default `Sheet1`). A workbook
with a different layout needs adaptation; an arbitrary spreadsheet will not work.

Formulas in read data cells and protected worksheets are rejected. The
company-account workbook filename named in tracker.py is outside scope.
Workbook paths are configured by the host, never supplied by an MCP tool caller.

## 4. Choose a client

### Native Codex

Merge the following into the client's existing `~/.codex/config.toml`,
preserving unrelated settings. Replace every `C:/YOUR_...` placeholder with
an absolute path on your machine; forward slashes avoid TOML backslash escaping.

```toml
[mcp_servers.application_tracker]
command = 'C:/YOUR_PROJECT/.venv/Scripts/python.exe'
args = ['C:/YOUR_PROJECT/mcp/server.py']

[mcp_servers.application_tracker.env]
APPLICATION_TRACKER_PATH = 'C:/YOUR_DATA/applications.xlsx'
APPLICATION_TRACKER_SHEET = 'Sheet1'
```

The same template is available as
[codex-config.example.toml](codex-config.example.toml). Reload the configured
server/client as needed, inspect its tool catalog, and ask for a read-only
lookup. Retain the actual tool call; merely starting Python proves no agent use.

### VS Code Copilot

The separate workspace template is
[.vscode/mcp.json](../.vscode/mcp.json). Its interpreter and server paths use
`${workspaceFolder}`; replace the workbook placeholder and sheet name.
Start the server from VS Code's MCP controls, enable its tool in Agent chat,
and verify an actual read-only call.

Native Codex model invocation, native automatic skill loading and VS Code UI
invocation were not confirmed in the recorded environment. These are
installation options, not claims of completed native-client demonstrations.

### Explicit CLI adapter used in the recorded runs

The recorded working path uses `mcp/client.py`, a JSON-configured stdio client
invoked explicitly by the Codex Work agent. It is not native Codex registration.

Create an ignored private configuration:

```powershell
New-Item -ItemType Directory -Force .local-tests | Out-Null
Copy-Item mcp/client-config.example.json .local-tests/client-config.json
```

Edit `.local-tests/client-config.json` before running the client. Replace the
command, server and workbook paths with real absolute paths. After installing
the checker in step 2, use the installed skill directory as shown below:

```json
{
  "command": "C:/YOUR_PROJECT/.venv/Scripts/python.exe",
  "args": ["C:/YOUR_PROJECT/mcp/server.py"],
  "skills_directories": ["C:/YOUR_PROJECT/.agents/skills"],
  "env": {
    "APPLICATION_TRACKER_PATH": "C:/YOUR_DATA/applications.xlsx",
    "APPLICATION_TRACKER_SHEET": "Sheet1"
  }
}
```

Avoid listing both the source and installed directories when they contain the
same skill name: the client requires one uniquely named match. Its small
frontmatter reader supports this project's single-line name/description fields,
not the full YAML language.

Discover the skills, load the checker, and inspect the actual MCP tool catalog:

```powershell
.\.venv\Scripts\python.exe mcp/client.py --config .local-tests/client-config.json skills
.\.venv\Scripts\python.exe mcp/client.py --config .local-tests/client-config.json skill acceptance-check
.\.venv\Scripts\python.exe mcp/client.py --config .local-tests/client-config.json list
```

Send a read-only query:

```powershell
'{"action":"query","company":"Example Co","limit":20}' | .\.venv\Scripts\python.exe mcp/client.py --config .local-tests/client-config.json call application_tracker
```

`Example Co` is illustrative; replace it with the organization you want to
look up. Zero matches can be a valid result. The client sends actual initialize,
initialized notification, tools/list and tools/call messages to the stdio server.
An agent must use the loaded skill instructions; printing them alone does not
perform a checker review.

Optional `--evidence PATH` saves a protocol record. Query links and notes are
omitted from its public projection, but company names, titles, dates, statuses
and other fields may still be private. Inspect/redact records before sharing.
Keep your local config, workbook and backups out of the public repository.

## Operations and boundaries

Queries use case-insensitive company/title/status substrings combined with AND.
Limit is 1–100; `total` and `truncated` expose omitted records. Resolve the
intended company and job before updating; substring searches can match others.

Updates require the row and matching current version returned by a query.
Only `new_status` and `new_notes` can be changed. Empty notes clears notes;
unspecified fields remain unchanged. Notes replace existing notes. The server
does not read email, submit applications, send messages or infer hiring outcomes.

Updates create an exact backup beside the configured file before replacement.
Formula-looking text remains literal text. Close Excel before writes: detected
Excel ownership, an existing cooperative MCP lock or a stale version blocks an
update. The lock does not coordinate unrelated writers; serialize writes with
other workflows. Backups contain the same private information as the source.

Test mutations on disposable copies. In addition to the synthetic suite, an
independent review verified a real-workbook-copy query/update/requery with the
original source unchanged. This is separate from unconfirmed native-client use.

The direct tools-only implementation supports protocol versions 2024-11-05,
2025-03-26 and 2025-06-18; other requests negotiate 2025-06-18. No full MCP
feature/client certification is claimed. References:
[stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports),
[Codex MCP](https://developers.openai.com/codex/mcp), and
[Codex skills](https://developers.openai.com/codex/skills).
