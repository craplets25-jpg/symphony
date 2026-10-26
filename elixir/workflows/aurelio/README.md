# Aurelio development runner

This manually supervised Symphony runner handles authorized issues in the
Aurelio Linear project. It uses the tested PR #2 app-server/checkouts foundation;
there is no second scheduler, automatic startup daemon or Shopify deployment.
Codespaces can stop after inactivity and are not a 24/7 hosting service.

See [LIFECYCLE-EVIDENCE.md](LIFECYCLE-EVIDENCE.md) for actual integration results
and [DEPENDENCY-REVIEW.md](DEPENDENCY-REVIEW.md) for remaining advisory exposure.

## Restore after restart or rebuild

Use the Symphony fork's `elixir` directory. Install mise from its official
installer if missing, reviewing the downloaded script before running it.
Until the setup PRs land, restore branch `chore/aurelio-development-lifecycle`;
a new Codespace on fork main will not automatically contain unmerged changes.

```sh
export PATH="$HOME/.local/bin:$PATH"
mise trust
mise install
mise exec -- mix local.hex --force
mise exec -- mix local.rebar --force
mise exec -- mix setup
mise exec -- mix build
mise exec -- make all
python3 -m unittest discover -s workflows/aurelio -p test_runner.py
python3 workflows/aurelio/runner.py skills
python3 workflows/aurelio/probe.py --skills
mise exec -- mix run --no-start workflows/aurelio/preflight.exs
```

The pinned runtime is OTP 28 and Elixir 1.19.5 for OTP 28. Restore dependencies
rather than copying credential/session caches. Inspect git status and fetch
updates before applying them; preserve existing user and issue work.

The `skills` command idempotently installs five symlinks in
`~/.agents/skills/aurelio-{linear,commit,pull,push,land}`, each pointing to the
unchanged upstream skill directory in this checkout's `.codex/skills`.
It preserves unrelated existing paths and refuses conflicts. Launcher and worker
both ensure installation before app-server starts. There are no discovery files
or untracked skill copies in an Aurelio checkout. After a rebuild, rerun this
command against the restored Symphony checkout. The isolated `skills/list` probe
must find exactly one enabled copy of each name; resolve collisions explicitly.

The probe injects all five actual skill items in a real inference turn, reads
Aurelio metadata through the connected native GitHub plugin and requires a
completed READY response. Initialization or stored-login status alone is not a
pass. Preflight uses Symphony's native `linear_graphql` binding and tracker reads,
checks project/gate/concurrency/sandbox, and exercises `Workspace.create_for_issue`
and the checkout hook. It removes only its own disposable preflight checkout and
requires no issue to be marked for execution. It does not dispatch or mutate Linear.

## Authentication and boundaries

Keep LINEAR_API_KEY, CODEX_ACCESS_TOKEN and AURELIO_REPO_TOKEN in Codespaces
secrets. Confirm presence with boolean-only checks, never environment dumps.
Use ChatGPT/Codex authentication, not a new Platform API key. Keep the connected
native GitHub plugin available to the account used by the Codex worker.

- **Tracker:** LINEAR_API_KEY stays host-side; workers use the injected
  linear_graphql tool. Raw tool access is token-scoped, not project-sandboxed,
  so the workflow restricts mutations to the assigned issue/workpad/attachment.
- **Git transport:** the dedicated Aurelio token must permit Contents read/write
  for craplets25-jpg/aurelio-trade. A worker receives it only as GH_TOKEN, with
  GH_REPO fixed to that repository. The process-local Git credential helper
  supplies it only for the exact HTTPS Aurelio path. No token enters Git URLs,
  command arguments or persisted repository/global configuration.
- **PR/review/merge:** use the connected native GitHub plugin. The current Git
  token can legitimately reject PR API access; do not broaden it merely to make
  gh PR commands work. The native plugin must independently prove its read/write
  capabilities. Skills retain their workflow, with native tool equivalents for
  GitHub API steps instead of a second PR manager.
- **Excluded:** host Linear, Shopify, ordinary Codespace GITHUB_TOKEN and unrelated
  secrets are not inherited by the worker. Only necessary Codex/Git authentication
  and runtime/proxy/certificate variables are allowed. This is an environment
  boundary, not a claim that raw tools or all host files are project-scoped.

The Codespaces non-secret SHELL_LOGGED_IN marker stays set; otherwise login
profiles redirect hooks/worker shells back to the Symphony source directory.
The real-login-shell regression test protects this behavior.

Rotate secrets in Codespaces settings, refresh the terminal/runtime, and rerun
probes. Newly declared additional-repository devcontainer permissions do not
grant access retroactively to an existing Codespace. Do not copy auth stores
or put credentials into scripts, Git, comments or screenshots.

## Start, observe and stop

```sh
python3 workflows/aurelio/runner.py start --port 4010 --logs-root ./log/aurelio
```

The foreground launcher supplies Symphony's required prototype acknowledgment;
the workspace-write sandbox and on-request policy still apply. Explicit turn
policy enables network access, with writable scope resolved from the issue cwd.
The worker selects Codex's supported automatic approvals reviewer. Ordinary
Git metadata writes still require sandbox escalation; the reviewer evaluates
them against the authorized issue instead of leaving Symphony waiting for an
interactive prompt. A denial must be recorded and handed off, not bypassed.
The checkout hook clones/fetches main, records its SHA, and preserves isolated
workspaces. Fetch refs and use one issue feature branch; never commit on main.
Existing issue workspaces survive review/restart and must not be reset blindly.

```sh
curl --fail --silent http://127.0.0.1:4010/api/v1/state
curl --fail --silent http://127.0.0.1:4010/api/v1/SHO-17
```

Keep the dashboard/API on loopback. Any Codespaces forwarding must remain
private. Save reviewed timestamped API snapshots and sanitized logs under
`elixir/log/` (ignored by Git); attach evidence to the private Linear workpad.
Use screenshots if an existing browser is available; never invent screenshots.

Stop with Ctrl-C, then verify the runner and its child PIDs exited and the port
closed. A supervising script should track descendants as well as its process
group: Erlang ports may have separate groups. Terminate only this run's remaining
children after identifying them; leave the Codespace's unrelated Codex host alone.

## Issue, PR and review lifecycle

All execution requires the exact project, active state and
`symphony-dispatch-approved`. Keep concurrency one. Use the actual existing
team status names (including spaces); no extra Linear statuses are required.

| Phase | Durable tracker representation |
| --- | --- |
| Ready | Todo + dispatch label |
| Working | In Progress + dispatch label |
| Review | In Review, dispatch removed; workpad links exact PR/head and checks |
| Rework | Todo + dispatch + symphony-rework-required; reuse branch/PR |
| Merge-only | Todo/In Progress + dispatch + symphony-merge-approved; workpad names approved head SHA |
| Substantive blocker | In Review + symphony-blocked, no dispatch/merge approval; exact paused action/decision |
| Merged, acceptance pending | In Review without dispatch; merge SHA and remaining acceptance in workpad |
| Accepted/completed | Done with lifecycle labels removed; verified acceptance, not only a completed turn |

Use the five skills. WORKFLOW.md explicitly adapts upstream Symphony examples:
Aurelio runs its documented npm/theme checks, not make/Mix commands. Pull a remote
feature branch only after it exists. Use native GitHub operations for PRs,
reviews, statuses, check runs and merge. The land watcher assumes gh API access
and CI, so use the skill's manual steps when those assumptions do not hold.

Review the exact current head, checks, feedback and actual GitHub requirements.
Do not invent a successful review or override branch protection. With no hosted
CI, state that explicitly and record local verification and review; absence of
checks is not green CI. Routine independent agent review can satisfy project
review policy when no human approval is required. Required human review remains
binding. Do not merge failing required checks or unreviewed failures. Use the
native merge tool's expected_head_sha to prevent merging an unreviewed new head.
No admin bypass, forced updates or auto-merge. Merging code does not deploy Shopify.

Record validation/review evidence before authorizing a merge phase. If an active
worker completes routine checks and independent review, it may proceed through
land without a redundant idle handoff; otherwise the coordinator reactivates
only the next authorized phase. Head changes invalidate merge-only approval.

Update the workpad first, then change state and remove dispatch in one mutation.
`max_turns: 8` is a turn limit per invocation, not a retry count. Symphony normally
queues a post-turn continuation check and retries eligible technical failures
with backoff. Review/blocked/completed tasks must lose eligibility. An operator
must stop an unreportable deterministic failure rather than leave it retrying.
Restart loses in-memory blocked claims; Linear state/labels are the durable stop.

## Aurelio delivery remains native Trade

SHO-1's sourced baseline audit is preserved. SHO-2 now reconciles the current
store with the verified baseline and reported five native configuration changes;
it does not acquire another theme. SHO-3 now verifies the explicit GitHub/CLI
handoff; it does not enable automatic synchronization. Original wording is
archived in their comments. Neither issue is automatically dispatched.

The next useful business workstream is SHO-4's authenticated B2B company/buyer
access journey, after necessary current-state readback and preceding blockers/
acceptance are resolved. Later native catalogs/pricing, ordering/templates,
taxes/markets/shipping and rendered desktop/mobile acceptance remain separate
issues. This runner setup does not establish an operational B2B store.

For authorized Shopify work identify store 84612481366 / aurelio-rb.myshopify.com
and current native Trade target before any operation. Preserve editor changes.
Use connected native Shopify capabilities where suitable; Theme Access permits
theme operations, not general Admin changes. SHOPIFY_CLI_THEME_TOKEN and optional
SHOPIFY_FLAG_STORE_PASSWORD must be supplied only when explicitly needed through
a supported scoped mechanism; they remain excluded from this generic Git worker.
No Lumen, custom theme code, historical pilot revival, real payments, customer
contact, ownership changes or commercial launch is authorized by runner setup.
