# Application tracker MVP acceptance criteria

Implementation contract prepared with AI assistance. This is not a student
submission narrative. It applies to this MCP component, not the HW7 game.

1. Expose exactly one MCP tool, `application_tracker`, over local stdio, with
   query and update actions. Support initialize, notification, list and call.
2. Read only the workbook and sheet configured by the host; do not accept a
   workbook path from the tool caller. Reject the company-account workbook and
   a sheet whose required row-5 headers do not match the application schema.
3. Query existing application rows with case-insensitive AND substring filters
   for company, title and status. Return total matches, up to 1–100 records,
   a truncation indicator, row identifiers and a workbook version.
4. Update only status (L) and notes (M) of an existing application row. Require
   the row and a matching current version from a query. Reject absent records,
   blank status, invalid text, no requested change fields and stale versions.
   Empty notes clears notes. Unspecified fields remain unchanged.
5. Back up the exact pre-update workbook before replacing it. Retain unrelated
   archive member contents and all worksheet bytes outside the targeted cells.
   Text starting with `=` remains text. Return the actual changes and backup.
6. Reject concurrent cooperative MCP writes and detected open-Excel ownership
   markers. Recheck the workbook version before replacement. Document that the
   MCP lock does not coordinate arbitrary external writers.
7. Provide a VS Code workspace stdio configuration and a separate Codex config
   example, with a working local interpreter and machine-specific paths marked
   in the setup instructions. No remote service or extension package is needed.
8. Demonstrate query/update/requery on disposable data through actual MCP wire
   messages. Verify compatibility using a copy of the real application workbook.
   Do not change real application outcomes for testing or claim an LLM/VS Code
   UI invocation from a subprocess smoke test.
