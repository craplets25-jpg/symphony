# Aurelio development lifecycle verification

Verified 26 October 2026. This extends the runner in
[Symphony PR #2](https://github.com/craplets25-jpg/symphony/pull/2), which remains
open. The follow-up branch is `chore/aurelio-development-lifecycle`, based on
PR #2's `710402212f5b3ec23c237a9fd17bf31eb5f0e222`. Neither setup PR is
merged automatically. Historical first-worker evidence stays in SETUP-EVIDENCE.md.

## Foundation and changes

PR #2 supplied authenticated app-server execution, the native after_create
checkout, command-scoped private Git credentials, filtered worker environment,
Codespaces login-shell cwd correction, native tracker polling/tool binding,
SHO-1 workpad handoff, manual launcher and readiness probes. Those mechanisms
remain in place.

The follow-up installs all five unchanged upstream skills through native shared
discovery; enables workspace-write implementation with Codex's built-in automatic
approval reviewer; supplies task-scoped Git write authentication; uses the native
GitHub plugin for PR operations; and defines review, rework, merge and blocked
handoffs with existing Linear statuses. There is one scheduler and one worker.

A real sandbox approval pause exposed an existing event-order defect: a generic
turn error overwrote approval/input blockers before orchestrator DOWN handling,
causing an error retry instead of a blocked state. The client now preserves the
specific blocker event. Focused tests exercise the client and actual orchestrator
state, including zero queued retry. No new retry subsystem was introduced.

## Verification matrix

| Check | Observed result |
| --- | --- |
| Runtime | mise 2026.10.19, Erlang/OTP 28.5, Elixir 1.19.5, Codex 0.164.0 |
| Repository gates | `mise exec -- make all`: exit 0; 305 tests, zero failures, six skipped; coverage, formatting, lint, specs and Dialyzer passed |
| Runner checks | Eight Python tests passed, including secret filtering, exact-repository Git helper, shared discovery, missing credential and real login-shell cwd |
| Skill discovery/invocation | An isolated app-server `skills/list` found exactly one enabled linear, commit, pull, push and land; all five actual skill items were supplied to a completed inference turn |
| Authenticated inference | Completed READY probe thread `01a178ae-cc38-7a12-b073-83a9df8df10b`; workers below completed real tasks |
| Linear tool | Workers read issue/blockers, reused the workpad, attached the PR, and atomically removed dispatch when handing off through injected `linear_graphql` |
| Git authentication | Real fetch, branch, commit and push to the private Aurelio repository; token remained outside URLs and persisted Git configuration |
| Native GitHub | Real private PR creation, review feedback, PR update and exact-head readback through the connected plugin; no broader PAT requested |
| Implementation/rework | Real worker runs on SHO-17 and the same checkout/branch/PR; fixture progressed from initial to verified; all 346 baseline hashes remained unchanged |
| Blocked dependency | SHO-17 Todo + dispatch remained idle while its synthetic predecessor SHO-16 was Backlog; predecessor then Canceled to release only the test |
| Approval/input blocker | Focused protocol/orchestrator tests prove blocked state, claim retained, no running worker and no retry; no claim of a live owner-decision test |
| Post-completion restart | Fresh Symphony process polled for 38 seconds with zero running/retrying/blocked agents; no duplicate dispatch; clean child-process shutdown |
| Authorized merge | Real Symphony worker used land/native GitHub to squash PR #18 into its scratch base; merge SHA `75e6c28e84c3aa0533ea5137849f42b3ec770086`; SHO-17 Done with no labels |
| Exact-head rejection | Native merge request with an intentionally wrong expected head returned HTTP 409 and did not merge |
| Security dependencies | Targeted supported updates remove 45 of 48 advisory findings; three explicitly classified residual reports remain; see DEPENDENCY-REVIEW.md |

One full-gate attempt failed a timer assertion in an existing continuation test
(451 ms remaining versus a 500 ms lower bound). A bounded full rerun passed.
An earlier lint failure on nesting in the blocker fix was corrected by extracting
a helper before the successful full gate. Failed commands are not counted as passes.

## Skills and permissions

Shared links `~/.agents/skills/aurelio-{linear,commit,pull,push,land}` resolve to
this Symphony checkout's `.codex/skills` directories. Both launcher and worker
ensure these links before app-server startup. No skill files are added to issue
checkouts. The runner refuses to replace conflicting user-owned paths. Rebuild
restoration and version-specific protocol details are in README.md.

Git transport receives only the dedicated Aurelio credential as GH_TOKEN through
an environment allowlist and exact-path, process-local helper. Host Linear,
Shopify, ordinary Codespace GitHub and unrelated credentials are excluded.
PR access uses the native GitHub plugin, as directed by the owner; the Git token's
PR API 403 is therefore not solved by broadening the token. Plugin/tool access is
not intrinsically project-limited: workflow scope and exact repository checks
remain necessary.

Upstream Git skills retain their implementations. Workflow instructions adapt
Symphony-specific test/template examples to Aurelio, avoid pulling nonexistent
feature refs, and use native GitHub equivalents. The land watcher's gh/hosted-CI
assumptions do not apply here; its manual review/merge steps do. No hosted CI
exists on the scratch PR: empty checks are not a successful CI run. Actual
required reviews and branch protection remain binding; no bypass is authorized.

## Controlled resources and acceptance

Only synthetic SHO-17 was dispatched for this setup. Synthetic SHO-16 tested a
blocker. The worker created [Aurelio PR #18](https://github.com/craplets25-jpg/aurelio-trade/pull/18)
from `symphony/lifecycle-test-20261026-head` into
`symphony/lifecycle-test-20261026-base`, never main. Reviewed head:
`26fbca9d58299feab34afed06ef2e720d9577cb3`. Independent coordinator review checked
the sole fixture file, all 346 captured native baseline hashes, clean checkout
and absence of persisted credentials. COMMENT reviews explicitly record feedback
and local independent review, not a fabricated formal self-approval.

The merge worker session was `01a179a6-657d-7221-906b-0af78407edc2` / turn
`01a179a6-7311-7423-8df7-55c84399888b`. It rechecked native GitHub reviews, the
approved head/base and local acceptance, performed the exact-head merge, fetched
and verified the merged commit and its parent/fixture/346 hashes, and changed
SHO-17 to Done with dispatch/merge labels removed atomically. The supervised
run ended with zero running/retrying/blocked agents and no remaining tracked
child processes. No business issue or Shopify target was changed.

Timestamped API snapshots, private execution logs and shutdown evidence are in
ignored `elixir/log/aurelio-lifecycle/`. These provide equivalent verifiable
state evidence; graphical screenshots were not captured. Do not commit raw
transcripts, credential/session stores or private workpad content.

## Reusable execution and next business task

`max_turns: 8` bounds continued turns within one worker attempt, not retries.
Native scheduling handles continuation/backoff; durable state/dispatch-label
transitions prevent redispatch after review, merge, completion and restart.
Read README.md's lifecycle table and start/observe/stop commands before selecting
one explicitly authorized issue. No daemon starts on Codespace startup.

SHO-2 and SHO-3 remain Backlog without dispatch. Their obsolete wording was
reconciled, with original descriptions archived in Linear comments: SHO-2 now
checks current native settings against the existing verified baseline; SHO-3
verifies explicit GitHub development and CLI handoff without automatic Shopify
GitHub synchronization. No second baseline was obtained. SHO-4's authenticated
B2B company/buyer journey is the next substantive implementation workstream,
after required SHO-2 current-state readback and dependency/acceptance review.
No business backlog item was activated by these integration tests.

This verifies development orchestration, not an operational B2B store. Later
Shopify CLI/theme credentials, current native editor state and target selection,
companies/buyers, catalogs/pricing, taxes/markets/shipping and an authorized test
buyer journey still require issue-scoped implementation and acceptance.
