# Iteration

> AI-assisted factual draft. The owner's independently written interpretation
> remains pending.

## Failure in the checker

The baseline checker marked update/preservation criteria MET from source
inspection. Its attempted tests did not reach assertions: the rule against any
project-file changes led it to copy a subset of source into a different scratch
directory, where permissions blocked fixture creation. It disclosed that limit,
but its preservation verdicts were wrong.

The first skill revision distinguished reviewed source/data from explicitly
allowed disposable outputs under an ignored scratch directory. It told the
checker to inspect test side effects and run safe tests in place rather than
copy only part of a project elsewhere. The earlier skill is preserved under
`evidence/acceptance-check-v2-before-scratch-revision.md`.

## The counterexample

The next fresh reviewer passed the old seven tests, then independently inspected
empty-cell boundaries. It found that the matcher could consume a following cell
when updating a self-closing target. Updating synthetic M8 deleted Q8's link;
updating an empty L6 deleted M6's notes. The original sparse-cell test checked
only the requested new note, missing loss of unrelated data.

The production pattern's greedy `[^>]*` could swallow the slash in `<c .../>`
and continue through the next cell's closing tag. A new regression reproduced
both failures against the old implementation before the fix.

## Changes and rerun

The matcher now uses non-greedy `[^>]*?`, ending at the first complete cell.
The new test compares every non-target worksheet byte and unrelated archive
member. Its literal boundary helper does not copy the production regex.

The checker skill was revised again: bounded-edit/preservation claims require
observed unrelated-content comparisons on relevant structural cases. Reading
back only the edited value cannot establish MET. Its previous wording is in
`evidence/acceptance-check-v3-before-preservation-revision.md`.

| Check | Before | After |
| --- | --- | --- |
| Original seven tests | Pass | Pass |
| New M8→Q8 and L6→M6 cases | Two failures | Both pass |
| Full suite | Eight tests, two failing subcases | Eight tests pass |
| Independent preservation review | NOT MET | MET |
| Real-workbook-copy check | Not rerun on this fix | Pass; exact backup and non-target preservation; original unchanged |

The published [failing](evidence/self-closing-regression-before.txt) and
[passing](evidence/self-closing-regression-after.txt) output uses synthetic data;
machine paths are replaced by PROJECT_ROOT. The real-copy verifier also needed
its old greedy comparison replaced with an independent boundary check. Its
separate openpyxl readback used an already-installed bundled interpreter; it is
not a new dependency of the server.

Finally, a new context discovered the final checker from client metadata and
reviewed the component without prior reports: all eight criteria MET, all eight
tests passed, plus an independent real-copy wire update/requery check. Original
bytes were unchanged. This does not prove every future checker judgment reliable.

## Client fallback

Native Codex server discovery succeeded, but model startup was blocked by the
terminal's network restriction. A background browser reached GitHub but timed
out reaching the local test page. The working fallback was a configured stdio
CLI adapter invoked explicitly by the agent, accurately identified in both
demonstrations rather than labeled native Codex registration.
