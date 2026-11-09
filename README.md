This project gives my coding agent two reusable tools: a skill for checking work against requirements, and an MCP tool for working with my existing application-tracking spreadsheet.

The idea came from something I kept running into across assignments. An agent could produce a working result, but I still had to explain what counted as finished, which requirements mattered, and what evidence I wanted to see. Meanwhile, useful information often lived outside the conversation, in files the agent needed a reliable way to query.

### Why I built it

During HW7, the inherited project contained conflicting requirements. I asked the agent to record those conflicts and follow the acceptance criteria:

“Keep a record of those inconsistencies, and implement the project according to its acceptance criteria.”

That instruction appears in my [HW7 prompt log](https://github.com/RyanZhou123232/chaos-lab-phase2/blob/main/prompt_log.md). A similar request appears in my [Naevia log](https://github.com/RyanZhou123232/Naevia/blob/main/prompt_log.md), where I asked whether the specification actually satisfied the handoff requirements.

The checker turns that recurring guidance into a reusable procedure. It reads the requirements, checks each criterion, and reports what is supported, missing, or still unverified. It also identifies conflicts and cites the relevant evidence. It reviews without fixing, so I can inspect its findings before deciding what to change.

The MCP tool handles a different need: structured access to existing information. In HW6, I asked to see exactly which records the retrieval pipeline returned. For HW8, I applied that same emphasis on traceable data to my application spreadsheet. The tool reads the workbook directly, so the agent can answer questions using recorded information instead of relying on conversation history.

### When to use it

The checker is useful after an agent implements a feature, when taking over someone else’s project, or before submitting an assignment. It works best when there is a clear specification to review against. Running it in a fresh session also gives the reviewer a chance to inspect the work without inheriting the doing agent’s assumptions.

The application tracker is useful for questions such as which applications match a company or role, or which records have a particular status. It can also update status and notes when a real change needs to be recorded. Updates require a current workbook version and create a backup. The tool maintains records; it does not submit applications or infer hiring outcomes.

The two components can work together: an agent queries the spreadsheet and produces a summary, then a separate checker compares that summary with the task requirements and returned evidence.

### What was tested

Two real application-review tasks were completed through the MCP client and checked in separate fresh-context sessions. The server’s eight automated tests passed, and updates were verified on a disposable copy of the real workbook.

Independent review also found a bug where updating an empty cell could remove neighboring content. That failure led to a regression test, a code fix, and stronger preservation rules in the checker.

The recorded demonstrations use an explicit command-line MCP client invoked by Codex Work. Native Codex registration and automatic skill loading remain unconfirmed.

Installation instructions are in [SETUP.md](mcp/SETUP.md). [DEMONSTRATION.md](DEMONSTRATION.md) records the two runs, and [ITERATION.md](ITERATION.md) explains the failure and fix. Public examples omit private application details.

### Sources and AI assistance

The checker started from the course’s *spec-check* example, with added rules for conflicting requirements, verification limits, and preservation of unrelated content.

AI helped implement the tools, develop tests, troubleshoot failures, and run independent reviews.

AI assisted with code, tests, troubleshooting, these drafts and independent
reviews. Reviewers started without doing-agent conversation or expected answers;
no different-model claim is made. The owner's agreement with a checker is not
generated or asserted here.
