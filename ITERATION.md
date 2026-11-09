# Iteration

The most useful failure in this project was a preservation bug that passed the original seven tests. It also exposed a weakness in how the checker decided that a requirement was met.

## The initial false pass

The baseline checker marked the update and preservation requirements as met after inspecting the source.

Its attempted tests had not reached their assertions. The skill’s instruction against changing project files led the reviewer to copy part of the project into another scratch directory, where permissions blocked test fixtures from being created.

The checker disclosed that limitation, but still gave preservation a passing judgment. A later counterexample showed that judgment was wrong.

The first skill revision clarified the boundary: reviewed source files and user data must remain unchanged, while explicitly allowed disposable test fixtures can be created in an ignored scratch directory. Suitable tests should run in place after their side effects are inspected.

## What the next review found

A fresh reviewer ran all seven existing tests successfully, then examined the empty-cell cases more closely.

The problem involved self-closing Excel cells. In this synthetic example, updating M8 should preserve Q8:

```xml
<c r="M8" s="0"/>
<c r="Q8" t="inlineStr">
  <is><t>KEEP</t></is>
</c>
```

The matching expression could accidentally consume both cells. Updating M8 could therefore remove Q8’s link. A similar case allowed an update to an empty status cell to remove the following notes cell.

The old sparse-cell test only checked whether the new note appeared. That assertion passed even when neighboring information disappeared.

## What changed

A new regression test reproduced both failures before the implementation was changed.

The matcher’s attribute scan was changed from greedy `[^>]*` to non-greedy `[^>]*?`, so it stopped at the first complete target cell. The regression also checked all worksheet bytes outside the target and the contents of unrelated archive members.

The checker skill received another revision: preservation claims now require observed comparisons of unrelated content, including relevant empty or missing structural cases. Reading back the edited value alone is insufficient.

## Results after the fix

| Check | Before | After |
| --- | --- | --- |
| Original seven tests | Passed | Passed |
| Two new neighboring-cell cases | Failed | Passed |
| Full suite | Eight tests with two failing subcases | Eight tests passed |
| Independent preservation review | NOT MET | MET |

The repaired implementation was also checked on a disposable copy of the real workbook. Query, update, and requery succeeded; the backup matched the original copy, unrelated content was preserved, and the actual source workbook remained unchanged.

A final fresh-context reviewer discovered and loaded the revised checker through the explicit client, passed all eight tests, and independently verified a real-workbook-copy update.

The important change was in the evidence required for a passing result: checking that the requested value appeared was expanded to checking that neighboring information survived.

## AI assistance

AI helped diagnose the failure, implement the repair, develop regression tests, and conduct independent reviews. This narrative is an AI-assisted reference draft.
