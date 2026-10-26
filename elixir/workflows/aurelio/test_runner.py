"""Security boundaries of the Aurelio command wrapper; no live credentials needed."""

import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).with_name("runner.py")


class RunnerTests(unittest.TestCase):
    def test_development_launcher_requires_the_dedicated_git_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(RUNNER), "start"],
                env={"HOME": directory, "PATH": str(Path(sys.executable).parent),
                     "LINEAR_API_KEY": "dummy-linear", "CODEX_ACCESS_TOKEN": "dummy-codex"},
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing AURELIO_REPO_TOKEN", result.stderr)
            self.assertFalse((Path(directory) / ".agents").exists())

    @unittest.skipUnless(Path("/etc/profile.d/codespaces.sh").exists(), "Codespaces login profile")
    def test_filtered_login_shell_stays_in_the_issue_workspace(self):
        spec = importlib.util.spec_from_file_location("aurelio_runner", RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["/bin/sh", "-lc", "pwd"], cwd=directory,
                env=runner.environment(), capture_output=True, text=True, check=True,
            )
            self.assertEqual(result.stdout.strip(), directory)

    def test_worker_drops_unrelated_secrets_and_preserves_codex_auth(self):
        with tempfile.TemporaryDirectory() as directory:
            codex = Path(directory, "codex")
            codex.write_text(
                f"#!{sys.executable}\nimport os,json\n"
                "print(json.dumps(dict(os.environ)))\n"
            )
            codex.chmod(0o700)
            env = {
                "PATH": directory,
                "HOME": directory,
                "CODEX_ACCESS_TOKEN": "dummy-codex",
                "LINEAR_API_KEY": "dummy-linear",
                "SHOPIFY_CLI_THEME_TOKEN": "dummy-shopify",
                "AURELIO_REPO_TOKEN": "dummy-source",
                "GITHUB_TOKEN": "dummy-github",
                "AWS_SECRET_ACCESS_KEY": "dummy-aws",
                "UNEXPECTED_SECRET": "dummy-other",
            }
            result = subprocess.run(
                [sys.executable, str(RUNNER), "worker"],
                env=env, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            child = json.loads(result.stdout)
            self.assertEqual(child["CODEX_ACCESS_TOKEN"], "dummy-codex")
            self.assertEqual(child["HOME"], directory)
            self.assertEqual(child.get("GH_TOKEN"), "dummy-source")
            self.assertEqual(child.get("GH_REPO"), "craplets25-jpg/aurelio-trade")
            for key in env.keys() - {"PATH", "HOME", "CODEX_ACCESS_TOKEN"}:
                self.assertNotIn(key, child)

    def test_credential_is_only_returned_for_exact_aurelio_https_path(self):
        for host, path, protocol, allowed in [
            ("github.com", "craplets25-jpg/aurelio-trade.git", "https", True),
            ("github.com", "craplets25-jpg/lumen.git", "https", False),
            ("example.com", "craplets25-jpg/aurelio-trade.git", "https", False),
            ("github.com", "", "https", False),
            ("github.com", "craplets25-jpg/aurelio-trade.git", "http", False),
        ]:
            with self.subTest(host=host, path=path, protocol=protocol):
                result = subprocess.run(
                    [sys.executable, str(RUNNER), "credential", "get"],
                    input=f"protocol={protocol}\nhost={host}\npath={path}\n\n",
                    env={"AURELIO_REPO_TOKEN": "dummy-source"},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual("password=dummy-source" in result.stdout, allowed)

    def test_shared_skills_are_installed_idempotently_without_checkout_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory, "skills")
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(RUNNER), "skills", str(root)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            for name in ["linear", "commit", "pull", "push", "land"]:
                self.assertTrue((root / f"aurelio-{name}" / "SKILL.md").is_file())
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["skills"])

    def test_shared_skill_install_preserves_an_existing_user_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owned = root / "aurelio-linear"
            owned.mkdir()
            sentinel = owned / "SKILL.md"
            sentinel.write_text("user-owned skill")
            result = subprocess.run(
                [sys.executable, str(RUNNER), "skills", str(root)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), "user-owned skill")

    def test_worker_git_credential_uses_only_exact_repository(self):
        for repository, expected in [
            ("craplets25-jpg/aurelio-trade.git", True),
            ("craplets25-jpg/lumen.git", False),
        ]:
            result = subprocess.run(
                [sys.executable, str(RUNNER), "credential", "get"],
                input=f"protocol=https\nhost=github.com\npath={repository}\n\n",
                env={"GH_TOKEN": "dummy-development"},
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual("password=dummy-development" in result.stdout, expected)

    def test_checkout_refuses_to_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory, "keep.txt")
            sentinel.write_text("existing work")
            result = subprocess.run(
                [sys.executable, str(RUNNER), "checkout"], cwd=directory,
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("empty workspace", result.stderr)
            self.assertEqual(sentinel.read_text(), "existing work")


if __name__ == "__main__":
    unittest.main()
