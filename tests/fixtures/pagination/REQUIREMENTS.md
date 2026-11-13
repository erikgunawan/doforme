# Requirement input supplied for the fixture

This is synthetic local fixture content, not a live external system export.

## Owner confirmation

The fixture owner confirms the business-document excerpt and acceptance criteria
below apply to ISSUE.md and are the current agreed scope for this exercise.
The supplied snapshot version is 2026-11-13-fixture. No real owner approval is implied.

## Business document excerpt — pagination rules

R1: page(items, index, size) returns up to size items from the zero-based page.
R2: The final page includes every remaining item. No item may be dropped.
Scope: non-negative page index and positive page size. Input validation is out of scope.

## Agreed acceptance criteria

AC1: page([1,2,3,4,5], 2, 2) returns [5].
AC2: page([1,2,3,4], 1, 2) returns [3,4].
AC3: page([1,2,3,4,5], 0, 2) returns [1,2].

No UI/layout requirement is in scope. Jira and Figma are not required sources for
this fixture because the confirmed local spec and criteria cover its scope.
