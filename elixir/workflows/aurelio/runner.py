#!/usr/bin/env python3
"""Manual Aurelio launcher, workspace hook and credential-filtered worker command."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


REPOSITORY = "https://github.com/craplets25-jpg/aurelio-trade.git"
HERE = Path(__file__).resolve().parent
ELIXIR = HERE.parent.parent
# An allowlist also excludes credentials added to the Codespace in the future.
RUNTIME_ENV = {
    "PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TERM",
    "TMPDIR", "TZ", "CODEX_HOME", "CODEX_ACCESS_TOKEN",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
}


def environment(extra=()):
    env = {key: value for key, value in os.environ.items() if key in RUNTIME_ENV | set(extra)}
    # Codespaces' /etc/profile.d/codespaces.sh otherwise changes login shells
    # back to the source repository, including Symphony's hook/worker shells.
    env["SHELL_LOGGED_IN"] = "true"
    return env


def credential(action):
    if action != "get":
        return
    fields = dict(line.rstrip("\n").split("=", 1) for line in sys.stdin if "=" in line)
    if (
        fields.get("protocol") == "https"
        and fields.get("host") == "github.com"
        and fields.get("path") == "craplets25-jpg/aurelio-trade.git"
        and os.environ.get("AURELIO_REPO_TOKEN")
    ):
        # Git consumes this pipe. Never invoke this mode interactively with real credentials.
        print("username=x-access-token")
        print("password=" + os.environ["AURELIO_REPO_TOKEN"])


def checkout():
    if any(Path.cwd().iterdir()):
        raise SystemExit("Checkout requires an empty workspace; preserving existing files")
    env = environment({"AURELIO_REPO_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"})
    env.pop("CODEX_ACCESS_TOKEN", None)
    env.pop("CODEX_HOME", None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    options = ["-c", "credential.useHttpPath=true", "-c", "credential.helper="]
    if env.get("AURELIO_REPO_TOKEN"):
        env.pop("GITHUB_TOKEN", None)
        env.pop("GH_TOKEN", None)
        helper = "!" + shlex.join([sys.executable, str(HERE / "runner.py"), "credential"])
    else:
        helper = "!gh auth git-credential"
    options += ["-c", "credential.helper=" + helper]
    git = ["git", *options]
    subprocess.run(
        [*git, "clone", "--single-branch", "--branch", "main", REPOSITORY, "."],
        env=env, check=True, timeout=120,
    )
    # The hook only runs for a new workspace, so this cannot reset previous issue work.
    subprocess.run([*git, "fetch", "origin", "main"], env=env, check=True, timeout=120)
    subprocess.run(["git", "merge", "--ff-only", "origin/main"], env=env, check=True)
    baseline = {
        "repository": REPOSITORY,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "workspace": str(Path.cwd()),
    }
    print("AURELIO_BASELINE " + json.dumps(baseline), flush=True)


def worker():
    os.execvpe("codex", ["codex", "app-server"], environment())


def start(arguments):
    for name in ("LINEAR_API_KEY", "CODEX_ACCESS_TOKEN"):
        if not os.environ.get(name):
            raise SystemExit(f"Missing {name}; no dispatch started")
    if not (ELIXIR / "bin/symphony").is_file():
        raise SystemExit("Build Symphony first with mise exec -- mix build")
    env = environment({"LINEAR_API_KEY", "AURELIO_REPO_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"})
    env["AURELIO_RUNNER"] = str(HERE / "runner.py")
    env["SYMPHONY_WORKSPACE_ROOT"] = os.environ.get(
        "SYMPHONY_WORKSPACE_ROOT", str(Path.home() / "code/aurelio-symphony-workspaces")
    )
    mise = shutil.which("mise") or str(Path.home() / ".local/bin/mise")
    os.chdir(ELIXIR)
    os.execvpe(mise, [
        mise, "exec", "--", "./bin/symphony", str(HERE / "WORKFLOW.md"),
        "--i-understand-that-this-will-be-running-without-the-usual-guardrails",
        *arguments,
    ], env)


if __name__ == "__main__":
    command, *arguments = sys.argv[1:]
    if command == "credential":
        credential(arguments[0])
    elif command == "checkout":
        checkout()
    elif command == "worker":
        worker()
    elif command == "start":
        start(arguments)
    else:
        raise SystemExit("Usage: runner.py {checkout|worker|start [Symphony options]}")
