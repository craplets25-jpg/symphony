# Aurelio setup verification — 26 October 2026

This report records checks performed in the GitHub Codespace. The private
[SHO-1 workpad](https://linear.app/workspace-ben/issue/SHO-1) holds the research
deliverable and private execution evidence. Runtime logs and API snapshots
are intentionally excluded from Git under `elixir/log/aurelio-setup/`.

| Check | Observed evidence |
| --- | --- |
| Starting checkout | Clean fork `main`, `ed669e7cf8840854ec66eaa769585df883f3793d`; dedicated branch `chore/aurelio-codespaces-runner` |
| Environment | Ubuntu 24.04.5, x86_64, 2 CPUs, approximately 8 GB RAM |
| Upstream specification | Local `SPEC.md` blob `cd24131a1e2358cbfecc4f6efb028fc9fc6edefc` matches official upstream `main` |
| Runtime | mise 2026.10.19; Erlang/OTP 28.5; Elixir 1.19.5 compiled for OTP 28 |
| Other tools | Git 2.55.0; GitHub CLI 2.100.0; Codex 0.164.0; Node 24.21.0; npm 11.19.0 |
| Installation | `mise trust`, `mise install`, Hex/Rebar installation, `mix setup`, `mix build`; real `bin/symphony` built |
| Main quality gate | `mise exec -- make all`: exit 0; format, lint/specs, coverage and Dialyzer passed |
| Tests | 305 tests, zero failures, six skipped opt-in external tests; 100% of configured coverage set |
| Wrapper checks | Four Python tests passed, including exact repository credential scope, unrelated-secret exclusion, file preservation and real Codespaces login-shell cwd |
| Network | Verified DNS, HTTPS responses and TLS validation to Linear, GitHub/API and Hex; successful runtime downloads and inference; no proxy required |
| Linear | Correct authenticated workspace, SHO team and Aurelio project; all 15 issues inspected; native active and terminal reads passed |
| GitHub | Existing normal Codespace credential could not read the private source; existing `AURELIO_REPO_TOKEN` succeeded without changing normal credentials |
| Source checkout | Clean Aurelio `main` at `97cd2fa9417c5479dfdac42d4254f0fc831c07c9`; exact remote has no credential; no persisted credential config |
| Native workspace hook | `Workspace.create_for_issue` invoked `after_create`, cloned/fetched source and returned a readable clean checkout; disposable preflight workspace removed |
| CLI inference | Real ephemeral read-only turn returned `READY`; thread `01a1786f-c8c0-7123-b89a-7afd727fcee0` |
| App-server inference | Initialize, ChatGPT account read, thread/turn start, completed `READY`, shutdown; thread `01a17872-01d9-74e0-99c7-da0168fcc160` |
| No-dispatch observation | Loopback dashboard HTTP 200; two API snapshots across the 30-second polling interval; zero running/retrying/blocked agents; no service errors |
| Real worker | SHO-1 alone; thread `01a1787c-eb71-7a31-9f65-d3ed4109f45c`, turn `01a1787c-ec91-7ec3-b2ee-4b42ef5a9a68`; service recorded completed session and agent run |
| Live credential boundary | App-server PID 15053 had Codex authentication and no Linear, Shopify, source-repository or GitHub token variables |
| Pilot deliverable | Existing workpad updated and read back; 346 baseline hashes verified; SHO-1 moved to In Review with dispatch label removed |
| Other issues | SHO-2 through SHO-15 remained in Backlog without the dispatch label |
| Shutdown | Supervised Symphony PID 14966, app-server PID 15053 and worker helper PID 15502 absent after stop; Aurelio checkout clean |
| Restart safety | A fresh supervised run after handoff stayed at zero running/retrying/blocked agents across another polling interval, then stopped |

## Repairs demonstrated by real failures

The initial exploratory app-server metadata probe incorrectly combined a
buffered text reader with descriptor readiness checks. A two-line reproduction
showed unread JSON could remain in Python's buffer while `select` reported no
readable descriptor. `probe.py` continuously reads messages on a dedicated
thread. Both the account response and actual inference now pass.

The first supervised SHO-1 attempt failed in the checkout hook before Codex
started. Filtering the host environment omitted `SHELL_LOGGED_IN`; the
Codespaces login profile changed cwd back to Symphony. The empty-workspace
guard refused to clone there. The observer stopped the process before its
retry, and dispatch eligibility was removed. No files were overwritten. A
failing real-login-shell regression test established the cause; setting the
non-secret marker fixed it. The native preflight passed under the corrected
filtered environment before one bounded second attempt.

The second attempt completed its real Codex turn and source audit. Symphony
then queued its normal post-turn active-state continuation check. The bounded
observer stopped at that boundary with exit 1; this was not a worker failure.
The service log records successful completion, and native Linear readback
confirmed In Review with no dispatch label. No second worker was dispatched.
The audit remains subject to owner review; it is not marked Done.

## Limits of the checks

Hex reported security advisories against existing locked upstream dependencies.
The lockfile was preserved; passing CI does not resolve those advisories. The
dashboard remains loopback-only. Dependency remediation is separate work.

No graphical browser was installed, so evidence uses real timestamped API
snapshots, worker process checks, execution records and the Linear workpad.
No screenshot, Shopify readback, theme upload or operational B2B-store
acceptance is claimed by the orchestration checks.

The Codespace process is manually supervised and does not automatically resume
dispatch after restart. See [the operator guide](README.md) for recovery,
credential rotation, dispatch removal and owner review.
