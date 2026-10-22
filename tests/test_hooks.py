import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "hooks" / "scripts"


def run_hook(name, event, root, env=None):
    merged = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    merged.pop("RELEASE_AUTHORIZED", None)
    if env:
        merged.update(env)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=root,
        env=merged,
        timeout=60,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def edit_event(path):
    return {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": path}}


def bash_event(command):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}


class HookCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.addCleanup(self.tmp.cleanup)

    def configure(self, **config):
        (self.root / ".claude").mkdir(exist_ok=True)
        (self.root / ".claude" / "toolkit.json").write_text(json.dumps(config))

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)

    def init_repo(self):
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        (self.root / "README.md").write_text("hello\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "init")


class NoConfigTests(HookCase):
    def test_every_hook_is_silent_without_config(self):
        (self.root / "secret.txt").write_text("x")
        for name, event in (
            ("protect_paths.py", edit_event("db/migrations/1.sql")),
            ("lock_tests.py", edit_event("tests/test_a.py")),
            ("deploy_gate.py", bash_event("npm run deploy")),
            ("secret_guard.py", bash_event("git commit -m x")),
            ("ticket_sync.py", bash_event("git commit -m x")),
            ("format_lint.py", edit_event(str(self.root / "secret.txt"))),
        ):
            code, out, err = run_hook(name, event, self.root)
            self.assertEqual((code, out, err), (0, "", ""), name)

    def test_malformed_config_is_reported_and_ignored(self):
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "toolkit.json").write_text("{not json")
        code, _, err = run_hook("protect_paths.py", edit_event("x"), self.root)
        self.assertEqual(code, 0)
        self.assertIn("could not read", err)


class ProtectPathsTests(HookCase):
    def test_blocks_directory_prefix_glob_and_bare_name(self):
        self.configure(protectedPaths=["db/migrations/", "*.lock", ".env"])
        for path in ("db/migrations/001.sql", str(self.root / "pnpm-lock.lock"), "config/.env"):
            code, _, err = run_hook("protect_paths.py", edit_event(path), self.root)
            self.assertEqual(code, 2, path)
            self.assertIn("is protected", err)

    def test_allows_other_paths(self):
        self.configure(protectedPaths=["db/migrations/"])
        code, out, err = run_hook("protect_paths.py", edit_event("db/seeds/a.sql"), self.root)
        self.assertEqual((code, out, err), (0, "", ""))

    def test_ignores_events_without_a_path(self):
        self.configure(protectedPaths=["db/"])
        code, _, _ = run_hook("protect_paths.py", {"tool_input": {}}, self.root)
        self.assertEqual(code, 0)


class LockTestsTests(HookCase):
    def test_only_blocks_while_marker_exists(self):
        self.configure(testGlobs=["tests/"])
        code, _, _ = run_hook("lock_tests.py", edit_event("tests/test_a.py"), self.root)
        self.assertEqual(code, 0)
        (self.root / ".claude" / ".tests-locked").write_text("")
        code, _, err = run_hook("lock_tests.py", edit_event("tests/test_a.py"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("tests are locked", err)
        code, _, _ = run_hook("lock_tests.py", edit_event("src/a.py"), self.root)
        self.assertEqual(code, 0)

    def test_default_globs_apply_when_none_configured(self):
        self.configure()
        (self.root / ".claude" / ".tests-locked").write_text("")
        for path in ("src/a.test.ts", "pkg/foo_test.go", "spec/thing.rb", "src/__tests__/x.js"):
            code, _, _ = run_hook("lock_tests.py", edit_event(path), self.root)
            self.assertEqual(code, 2, path)
        code, _, _ = run_hook("lock_tests.py", edit_event("src/thing.ts"), self.root)
        self.assertEqual(code, 0)


class DeployGateTests(HookCase):
    def test_blocks_matching_command_until_authorised(self):
        self.configure(gatedCommands=["^(npm|pnpm) run deploy", "terraform apply"])
        code, _, err = run_hook("deploy_gate.py", bash_event("npm run deploy -- --prod"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("release authorisation", err)
        code, _, _ = run_hook("deploy_gate.py", bash_event("npm run deploy"), self.root, env={"RELEASE_AUTHORIZED": "1"})
        self.assertEqual(code, 0)
        (self.root / ".claude" / ".release-authorized").write_text("")
        code, _, _ = run_hook("deploy_gate.py", bash_event("terraform apply"), self.root)
        self.assertEqual(code, 0)

    def test_block_names_both_authorisation_routes(self):
        """The README documents two routes; the block message must name both so a blocked agent can relay them."""
        self.configure(gatedCommands=["^git tag "])
        code, _, err = run_hook("deploy_gate.py", bash_event("git tag v1.0.0"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("RELEASE_AUTHORIZED=1", err)
        self.assertIn(".claude/.release-authorized", err)
        self.assertIn("one-way door", err)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("`RELEASE_AUTHORIZED`", readme)
        self.assertIn("`.claude/.release-authorized`", readme)

    def test_non_matching_and_invalid_patterns(self):
        self.configure(gatedCommands=["[unclosed", "terraform apply"])
        code, _, err = run_hook("deploy_gate.py", bash_event("terraform plan"), self.root)
        self.assertEqual(code, 0)
        self.assertIn("invalid regex", err)


class SecretGuardTests(HookCase):
    def test_blocks_staged_credential_and_names_the_line(self):
        self.init_repo()
        self.configure(secretAllowlist=["tests/fixtures/"])
        (self.root / "config.py").write_text("DEBUG = True\nAWS_KEY = 'AKIAJ4QX7ZK2M9P3T6RQ'\n")
        self.git("add", "config.py")
        code, _, err = run_hook("secret_guard.py", bash_event("git commit -m 'add config'"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("config.py:2", err)
        self.assertIn("AWS access key", err)
        self.assertNotIn("AKIAJ4QX7ZK2M9P3T6RQ", err)

    def test_allowlisted_paths_placeholders_and_non_commits_pass(self):
        self.init_repo()
        self.configure(secretAllowlist=["tests/fixtures/"])
        fixtures = self.root / "tests" / "fixtures"
        fixtures.mkdir(parents=True)
        (fixtures / "keys.txt").write_text("-----BEGIN RSA PRIVATE KEY-----\n")
        (self.root / "settings.py").write_text('api_key = "your-api-key-here"\n')
        self.git("add", "tests", "settings.py")
        code, _, _ = run_hook("secret_guard.py", bash_event("git commit -m ok"), self.root)
        self.assertEqual(code, 0)
        (self.root / "x.py").write_text("password = 'hunter2hunter2'\n")
        self.git("add", "x.py")
        code, _, _ = run_hook("secret_guard.py", bash_event("git status"), self.root)
        self.assertEqual(code, 0)

    def test_commit_all_scans_unstaged_tracked_changes(self):
        self.init_repo()
        self.configure()
        (self.root / "README.md").write_text("token = 'ghp_" + "a" * 36 + "'\n")
        code, _, _ = run_hook("secret_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 0)
        code, _, err = run_hook("secret_guard.py", bash_event("git commit -am x"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("GitHub token", err)


class TicketSyncTests(HookCase):
    def add_ticket(self, status):
        folder = self.root / "docs" / "changes" / "0002-thing" / "tickets"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "T1-a.md").write_text(f"---\nid: T1\ntitle: A\nblocked_by: []\nfiles: [src/a.py]\nproves: x\nstatus: {status}\n---\n")

    def test_asks_when_source_staged_without_change_folder(self):
        self.init_repo()
        self.configure()
        self.add_ticket("in-progress")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n")
        self.git("add", "src/a.py")
        code, out, _ = run_hook("ticket_sync.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertIn("0002-thing", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_silent_when_change_folder_staged_too_or_nothing_in_progress(self):
        self.init_repo()
        self.configure()
        self.add_ticket("in-progress")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n")
        self.git("add", "src/a.py", "docs")
        code, out, _ = run_hook("ticket_sync.py", bash_event("git commit -m x"), self.root)
        self.assertEqual((code, out), (0, ""))
        self.add_ticket("done")
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "ticket")
        (self.root / "src" / "a.py").write_text("x = 2\n")
        self.git("add", "src/a.py")
        code, out, _ = run_hook("ticket_sync.py", bash_event("git commit -m x"), self.root)
        self.assertEqual((code, out), (0, ""))


PY = shlex.quote(sys.executable)


def feedback(code, output="", marker=None):
    """A shell command that prints `output`, optionally touches `marker`, and exits with `code`."""
    touch = f"open({marker!r}, 'w').close(); " if marker else ""
    return f'{PY} -c "{touch}print({output!r}); raise SystemExit({code})"'


class RedGuardTests(HookCase):
    def test_blocks_commit_on_red_and_passes_on_green(self):
        self.init_repo()
        red = feedback(1, "boom")
        self.configure(feedbackCommand=red)
        (self.root / "app.py").write_text("x = 1\n")
        self.git("add", "app.py")
        code, out, err = run_hook("red_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn(red, err)
        self.assertIn("Exit code: 1", err)
        self.assertIn("boom", err)
        self.assertIn("red", err)
        self.configure(feedbackCommand=feedback(0, "fine"))
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))

    def test_non_commits_and_unconfigured_repos_never_run_the_feedback_command(self):
        self.init_repo()
        marker = self.root / "ran"
        (self.root / "app.py").write_text("x = 1\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))
        self.configure(feedbackCommand="")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))
        self.configure(feedbackCommand=feedback(1, marker=str(marker)))
        self.assertEqual(run_hook("red_guard.py", bash_event("git status"), self.root), (0, "", ""))
        self.assertFalse(marker.exists())

    def configure_committed(self, **config):
        self.configure(**config)
        self.git("add", ".claude")
        self.git("commit", "-q", "-m", "config")

    def test_only_workflow_documents_and_tests_skip_the_check(self):
        self.init_repo()
        marker = self.root / "ran"
        self.configure_committed(feedbackCommand=feedback(1, "boom", marker=str(marker)), testGlobs=["tests/"])
        (self.root / "docs" / "changes" / "0009-x").mkdir(parents=True)
        (self.root / "docs" / "changes" / "0009-x" / "intent.md").write_text("# Intent\n")
        (self.root / "GLOSSARY.md").write_text("# Glossary\n")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_x.py").write_text("assert False\n")
        self.git("add", "docs", "GLOSSARY.md")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))
        self.assertFalse(marker.exists())
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 2)
        self.assertTrue(marker.exists())
        self.assertIn("boom", err)

    def test_staged_and_unstaged_source_changes_both_count(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1))
        (self.root / "README.md").write_text("changed\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -am x"), self.root)[0], 2)
        self.git("add", "README.md")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root)[0], 2)

    def test_paths_with_spaces_and_nested_workflow_names_are_classified(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1), testGlobs=["tests/"])
        (self.root / "docs").mkdir()
        (self.root / "docs" / "my notes.md").write_text("x\n")
        (self.root / "REVIEW.md").write_text("x\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))
        (self.root / "lib").mkdir()
        (self.root / "lib" / "GLOSSARY.md").write_text("x\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root)[0], 2)
        (self.root / "lib" / "GLOSSARY.md").unlink()
        (self.root / "my app.py").write_text("x = 1\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root)[0], 2)

    def test_renaming_source_into_docs_still_runs_the_check(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1))
        (self.root / "docs").mkdir()
        self.git("mv", "README.md", "docs/README.md")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root)[0], 2)

    def test_checks_the_worktree_the_commit_lands_in(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(0))
        (self.root / ".git" / "info" / "exclude").write_text(".claude/worktrees/\n")
        worktree = self.root / ".claude" / "worktrees" / "w1"
        self.git("worktree", "add", "-q", str(worktree), "-b", "w1")
        (worktree / ".claude" / "toolkit.json").write_text(json.dumps({"feedbackCommand": feedback(1, "worktree is red")}))
        (self.root / "app.py").write_text("x = 1\n")
        self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""))
        in_worktree = {**bash_event("git commit -m x"), "cwd": str(worktree)}
        for event in (
            in_worktree,
            bash_event("git -C .claude/worktrees/w1 commit -m x"),
            bash_event(f"git -C {worktree} commit -m x"),
            bash_event("cd .claude/worktrees/w1 && git add -A && git commit -m x"),
        ):
            code, _, err = run_hook("red_guard.py", event, self.root)
            self.assertEqual(code, 2, event)
            self.assertIn("worktree is red", err)

    def test_quotes_only_the_last_forty_lines(self):
        self.init_repo()
        self.configure(feedbackCommand=f"{PY} -c \"print('\\n'.join('line %d' % i for i in range(100))); raise SystemExit(3)\"")
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("Exit code: 3", err)
        self.assertIn("line 99", err)
        self.assertIn("line 60\n", err)
        self.assertNotIn("line 59\n", err)


class FormatLintTests(HookCase):
    def test_runs_matching_formatter_and_surfaces_linter_failure(self):
        marker = self.root / "formatted.txt"
        self.configure(
            formatters={"*.{py,md}": f"{sys.executable} -c \"open('{marker}', 'w').write('{{file}}')\""},
            linters={"*.py": f"{sys.executable} -c \"import sys; print('E302 blank lines'); sys.exit(1)\""},
        )
        target = self.root / "src" / "a.py"
        target.parent.mkdir()
        target.write_text("x=1\n")
        code, _, err = run_hook("format_lint.py", edit_event(str(target)), self.root)
        self.assertEqual(code, 2)
        self.assertTrue(marker.exists())
        self.assertIn("linter failed for src/a.py", err)
        self.assertIn("E302 blank lines", err)

    def test_silent_on_success_and_for_unmatched_files(self):
        self.configure(formatters={"*.py": "true"}, linters={"*.py": "true"})
        target = self.root / "a.py"
        target.write_text("")
        code, out, err = run_hook("format_lint.py", edit_event(str(target)), self.root)
        self.assertEqual((code, out, err), (0, "", ""))
        other = self.root / "a.txt"
        other.write_text("")
        code, out, err = run_hook("format_lint.py", edit_event(str(other)), self.root)
        self.assertEqual((code, out, err), (0, "", ""))

    def test_missing_file_is_ignored(self):
        self.configure(formatters={"*": "false"})
        code, _, _ = run_hook("format_lint.py", edit_event("gone.py"), self.root)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
