---
name: acceptance-check
description: Review a project's implementation against its acceptance criteria, identify conflicting requirements, and report evidence without changing files. Use when asked to check a project against SPEC.md, verify acceptance criteria, or review readiness for submission.
---

# Acceptance Check

Review only. Do not edit reviewed source or data, fix issues, install dependencies,
or commit changes. Existing tests may create disposable fixtures in an explicitly
allowed, ignored scratch directory; that is not permission to change source.

## Procedure

1. Read the specified requirements file, or `SPEC.md` in the project root. If neither is available, ask for the requirements rather than inventing criteria.
2. Extract every acceptance criterion, preserving its identifier and priority. Split compound criteria into subchecks without dropping conditions.
3. Compare the criteria with other relevant requirements and record conflicts. Apply the user's explicitly stated precedence when available. Otherwise, mark affected criteria BLOCKED and ask which requirement governs; continue checking unaffected criteria. Do not silently prefer the README, prose, or numbered criteria.
4. Inspect the implementation and relevant tests for each criterion. Treat documentation and comments as claims, not proof. Check whether test expectations come from the requirements or merely repeat implementation constants.
5. Inspect test side effects before running relevant existing checks. Run them in place when they preserve reviewed source/data and confine disposable fixtures to an explicitly allowed ignored scratch directory. Do not copy a partial project merely to avoid temporary test files; changing location can change the behavior under review. If the host denies scratch access, report an environment block, not a behavior failure. Never install anything. Distinguish source inspection, observed results, and behavior still needing browser or manual verification.
6. Report all criteria and the three highest-priority gaps, or fewer if fewer exist. Recommend next actions without performing them.

## Status rules

- MET: Evidence supports every part of the criterion at the required verification level.
- For a compound criterion, assign MET only when every subcheck is verified. If logic passes but required visual feedback is unobserved, assign PARTIAL to the whole criterion; a caveat after MET does not resolve missing verification.
- PARTIAL: Some parts are supported, but others are missing or unverified.
- NOT MET: Evidence shows the required behavior is absent or incorrect.
- BLOCKED: Missing access, requirements, or an unresolved conflict prevents a judgment.
- Do not claim tests passed unless you ran them in this review. Label earlier results as reported history.
- Do not claim visible behavior works from source inspection alone. Name the remaining visual or interaction check.
- Cite implementation file paths and line numbers for every MET claim. Explain missing evidence explicitly.
- Before reporting, reconcile statuses with verification limits. Downgrade any MET whose evidence still lists a required condition as unverified.

## Output format

Start with `Requirements: <path>` and `Precedence: <explicit decision or unresolved>`.

Then list conflicts, or write `Conflicts: none found`:

`CONFLICT <id>: <source:line and value> vs <source:line and value>; resolution: <decision or BLOCKED>`

Use one line per criterion:

`[MET | PARTIAL | NOT MET | BLOCKED] #<id>: <criterion> | Evidence: <path:line and finding, or missing evidence> | Verification: <source inspection / command and observed result / not run and reason>`

Finish with `Priority gaps:` and up to three concrete gaps, followed by `Verification limits:` describing anything not checked. If there are no gaps or limits, state that explicitly.
