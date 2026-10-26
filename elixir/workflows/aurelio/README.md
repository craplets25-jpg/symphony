# Aurelio Codespace operator guide

This is a manually supervised Symphony runner for the Aurelio Linear project.
It is currently restricted to the read-only SHO-1 pilot. It does not start on
Codespace boot and is not a 24/7 service. Codespaces can stop after inactivity.

## Restore the runtime

From the Symphony fork's `elixir` directory, install mise from its official
installer at <https://mise.jdx.dev/getting-started.html> if absent. Review the
downloaded installer before running it. Then:

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
```

`mise.toml` selects OTP 28 and Elixir 1.19.5 for OTP 28. The verified OTP patch
is recorded in the setup evidence. Restore dependencies after a rebuild; do
not copy caches or sessions into Git. Review `git status` and fetch the fork
before updating, preserving local changes. Do not reset an issue checkout to
make it appear clean.

## Credentials and preflight

Keep `LINEAR_API_KEY` and `CODEX_ACCESS_TOKEN` in Codespaces secrets. Prefer
ChatGPT authentication; this runner does not use a Platform API key. Confirm
presence without printing values:

```sh
python3 -c 'import os; [print(k, "SET" if os.environ.get(k) else "MISSING") for k in ("LINEAR_API_KEY", "CODEX_ACCESS_TOKEN", "AURELIO_REPO_TOKEN")]'
python3 workflows/aurelio/probe.py
mise exec -- mix run --no-start workflows/aurelio/preflight.exs
```

The probe must complete an actual app-server turn returning READY; initialization
and stored-login status are insufficient. It excludes unrelated secrets, uses
a disposable read-only workspace, and stops its child process group.

Preflight validates the workflow, authenticates via Symphony's own
`linear_graphql` binding, checks all 15 project issues for zero eligibility,
performs native active/terminal-state reads and exercises the actual
`Workspace.create_for_issue`/`after_create` path. It removes only the disposable
workspace it just created. It does not start a scheduler or mutate Linear.

The checkout hook first uses `AURELIO_REPO_TOKEN` when supplied; otherwise it
uses the existing GitHub CLI authorization for that command. Prefer a
fine-grained token for this exact repository with Contents: read, or supported
Codespaces additional-repository read access. Declaring additional permissions
in a devcontainer does not retroactively grant them to an existing Codespace.
The credential helper returns a token only for HTTPS and the exact Aurelio
repository path. Git URLs and repository config contain no token. The hook
clones `main`, fetches it, fast-forwards and logs the baseline SHA in a new
issue workspace. It refuses to overwrite existing files.

The worker environment is an allowlist. It retains Codex authentication,
ordinary runtime paths and proxy/certificate settings; it excludes Linear,
Shopify, GitHub, source-repository and unrelated secrets. Linear operations
use Symphony's host-side dynamic tool. This tool's API access is limited by
the token's permissions, not by the project slug; the prompt also confines it
to SHO-1. The label is a scheduler gate, not a general Linear authorization boundary.

The wrapper sets Codespaces' non-secret `SHELL_LOGGED_IN=true` marker. Without
it, the Codespace login profile redirects Symphony's hook and worker shells
to the original source repository. A regression test checks a real login shell
stays inside its issue workspace. Do not remove this marker from the filter.

Rotate credentials in Codespaces secret settings, restart the terminal or
Codespace so the process receives the replacements, and repeat both probes.
Never print tokens, copy auth caches, or put credential literals in a workflow.

## Start, observe and stop

Keep all issues ineligible for the first observation run:

```sh
python3 workflows/aurelio/runner.py start --port 4010 --logs-root ./log/aurelio
```

This foreground launcher supplies the executable's required prototype
acknowledgment flag; the explicit read-only sandbox and approval policy still
apply. The dashboard listens at `127.0.0.1:4010`; leave any Codespaces port
forwarding private. Do not expose this unauthenticated API publicly.

In another terminal:

```sh
curl --fail --silent http://127.0.0.1:4010/api/v1/state
curl --fail --silent http://127.0.0.1:4010/api/v1/SHO-1
```

Save timestamped API snapshots and sanitized logs under `elixir/log/`, which
Git ignores. Capture real dashboard screenshots if an existing browser is
available; otherwise retain API evidence and state clearly that no screenshot
was taken. Review artifacts before attaching them to Linear. Never attach
the Codex home, auth cache, full environment or unreviewed transcripts.

Stop with Ctrl-C in the foreground terminal; confirm the process exits. Check
for surviving `beam.smp` and worker `codex` processes and verify their PIDs and
parentage before terminating only this run's children. An operator supervising
through a script should create a new process group, send SIGTERM to that group,
wait, and use SIGKILL only if that same group fails to stop. Do not kill the
Codespace's unrelated Codex host process.

## Approve exactly one issue

Only after inference, checkout and no-dispatch polling pass, re-read SHO-1's
project, description, blockers, labels and existing workpad. The authorized
first task is read-only baseline/workflow research. Change SHO-1 to Todo and
add `symphony-dispatch-approved`; preserve other labels. Verify no other issue
is eligible, then launch and observe exactly one claim and app-server session.

Use existing workpad `46e92d8e-a949-4bdd-b7a4-3f9975581926`. Preserve historical
observations and add the current environment and sourced findings. Completed
deliverables go to In Review with the dispatch label removed in the same issue
update. Verify this in Linear before stopping. Done requires owner acceptance.

`max_turns: 1` limits turns per invocation, not retries. A failed or normally
completed invocation can be rescheduled if its issue remains eligible. For a
blocked issue, record the gap, remove its dispatch label and move it to In
Review or Backlog as appropriate. Stop the supervised runner if it starts
retrying a persistent failure. Before restarting after any interruption, inspect
Linear and resolve eligible/blocked issues; in-memory blocked claims do not
survive restart. Check the existing issue workspace rather than deleting or
reusing another issue's checkout.

SHO-2 through SHO-15 remain undispatched. Before later work, reconcile SHO-2
against the existing verified baseline and SHO-3 against the accepted explicit
CLI workflow. Do not reacquire Trade or install automatic synchronization to
satisfy historical wording. Review the workflow's SHO-1-only restriction and
read-only policy explicitly before approving any future implementation issue.

## Later Shopify work

No Shopify credentials or operations are needed for this pilot. Later tasks
need the native Trade baseline, authorized Shopify CLI/Theme Access, explicit
`SHOPIFY_FLAG_STORE=aurelio-rb.myshopify.com`, exact theme/preview selection,
and preservation of current theme-editor changes. `SHOPIFY_CLI_THEME_TOKEN`
authorizes theme access, not general Admin operations. An optional
`SHOPIFY_FLAG_STORE_PASSWORD` serves applicable visitor-preview flows.

Subsequent issues cover B2B companies/buyers, native catalogs/contextual prices,
native ordering/templates, taxes/markets/shipping and an authorized test-buyer
journey. Use configure/test/fix cycles and rendered evidence. The existing
Trade theme `207023571286` is the last documented active development-store
theme; the historical custom pilot `209046962518` is not the implementation
target. No custom theme code, Lumen work, real payments, customer contact,
ownership changes or commercial launch is authorized by this runner setup.
