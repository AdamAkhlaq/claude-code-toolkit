import contextlib
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

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
            ("deploy_gate.py", bash_event("echo " + "{a,b}" * 14)),
            ("red_guard.py", bash_event("git commit -m x")),
            ("red_guard.py", bash_event("git commit -am " + "{a,b}" * 14)),
            ("secret_guard.py", bash_event("git commit -m x")),
            ("secret_guard.py", bash_event("git commit -m x; echo " + "{a,b}" * 14)),
            ("ticket_sync.py", bash_event("git commit -m x")),
            ("ticket_sync.py", bash_event("git commit -m x; echo " + "{a,b}" * 14)),
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

    def test_a_gated_command_is_caught_anywhere_in_the_line(self):
        self.configure(gatedCommands=["^git tag ", "^gh release "])
        for command in (
            "cd . && git tag v2",
            "true; git tag v3",
            "/usr/bin/git tag v4",
            'bash -c "git tag v5"',
            "git fetch -q && gh release create v6",
            "git fetch -q\ngit tag v7",
            "cat > notes.md <<'EOF'\nnotes\nEOF\ngit tag v8",
            'echo "a <<EOF"\ngit tag v9',
            "cat <<< x\ngit tag v10",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in ('echo "git tag v1"', "git log --grep 'git tag '", 'echo "notes\ngit tag v1"', "cat > notes.md <<'EOF'\ngit tag v1 is next\n| `/usr/bin/git tag v2` |\nEOF"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

    def test_the_shell_reader_keeps_every_command_boundary(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "true # note\ngit tag v1",
            "echo $((1<<2))\ngit tag v2",
            "# see <<EOF\ngit tag v3",
            "cat <<EOF\ngit tag v4",
            "true;>out git tag v5",
            "true&&>/dev/null git tag v6",
            "echo `git tag v7`",
            "echo $'it\\'s'; git tag v8",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)

    def test_the_shell_reader_splits_words_where_bash_does(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "echo a\\ #b; git tag v1",
            'x="a b"; echo ${x/ #/}; git tag v2',
            "echo $[1<<EOF]\ngit tag v3\nEOF",
            "git ta\\\ng v4",
            "bash -c -- 'git tag v5'",
            "bash -c -e 'git tag v6'",
            "ksh -c 'git tag v7'",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        command = "echo \"a git tag v1\" $'\\''"
        self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

    def test_a_substitution_the_shell_runs_is_read_whole(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "cat <<EOF\n$(git tag v1)\nEOF",
            "cat <<EOF\n`git tag v2`\nEOF",
            'echo "$(echo ")"; git tag v3)"',
            'echo "$(case a in a) git tag v4;; esac)"',
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in ("cat <<'EOF'\n$(git tag v1)\nEOF", 'cat <<"EOF"\n`git tag v1`\nEOF', "cat <<EOF\ngit tag v1\nEOF"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

    def test_the_reader_ends_quotes_heredocs_and_substitutions_where_bash_does(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "echo $'a\\'b'; git tag v1; echo 'c'",
            "echo $'\\''; git tag v1; echo \"'\"",
            "echo \"a\\\"b\" $'c\\'d'; git tag v1; echo \"'\"",
            "x=$'\\'' git tag v1; echo \"'\"",
            "cat <<E'OF'\nEOF\ngit tag v2\nE",
            'cat <<"E"OF\nEOF\ngit tag v2\nE',
            "cat <<E\\OF\nEOF\ngit tag v2\nE",
            "cat <<-E'OF'\n\tEOF\ngit tag v2\nE",
            "cat <<E:OF\nE:OF\ngit tag v3\nE",
            "cat <<E+OF\nE+OF\ngit tag v3\nE",
            "cat <<E$OF\nE$OF\ngit tag v3\nE",
            "echo `echo \\`git tag v4\\``",
            'echo "`echo \\`git tag v4\\``"',
            "echo `echo \\`echo \\\\\\`git tag v4\\\\\\`\\``",
            'x="$( : # )\ngit tag v5\n)"',
            "x=\"$(cat <<'E'\n)\nE\ngit tag v5\n)\"",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in ("cat <<E'OF'\ngit tag v6\nEOF", "cat <<E:OF\ngit tag v6\nE:OF", "echo \\`git tag v6\\`"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)
        for command in ("cat <<E\n" * 20_000 + "git tag v7", '"$(' + "cat <<E\n" * 20_000 + 'git tag v7)"', "".join(f"cat <<E{n}\n" for n in range(15_000)) + "git tag v7"):
            started = time.monotonic()
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command[:20])
            self.assertLess(time.monotonic() - started, 5, command[:20])

    def test_a_word_is_read_as_bash_expands_it(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "$'\\x67it' tag v1",
            "$'\\147it' tag v2",
            "$'\\u0067it' tag v2",
            "$'\\U00000067it' tag v2",
            "g$'\\x69't tag v2",
            "git $'\\x74ag' v2",
            "$'git\\0xyz' tag v2",
            "eval $'\\x67it tag v2'",
            "bash -c $'\\x67it tag v2'",
            "{git,tag} v3",
            "git {tag,v4}",
            "{git,} tag v5",
            "{,git} tag v5",
            "{g..g}it tag v6",
            "{git,tag,v6}",
            "{{git,tag},v6}",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        code, _, err = run_hook("deploy_gate.py", bash_event("echo " + "{a,b}" * 14 + " && git status"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("too long to read", err)
        for command in ("echo '{git,tag} v1'", 'echo "{git,tag}" v1', "echo $'{git,tag}' v1", "echo \\{git,tag} v1", "{ echo git; }", "gi{t,} tag v5", "{f..h}it tag v6", "mkdir -p src/{a,b} && cp app.py{,.bak}"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

    def test_the_reader_reads_its_own_edges_as_bash_does(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "echo $'\\c'; git tag v2; echo 'x'",
            "echo $'a\\c'; git tag v2; echo 'x'",
            "echo $'\\c\\\\'; git tag v2; echo 'x'",
            "echo $'\\c\\''; git tag v2; echo 'x'",
            "echo {W..a..5}'x'; git tag v3; echo 'y'",
            "echo {Z..a}'x'; git tag v3; echo 'y'",
            'echo {Z..a}"x"; git tag v3; echo "y"',
            "echo {a..W}'x'; git tag v3; echo 'y'",
            "echo {A..z..1}'x'; git tag v3; echo 'y'",
            "cat <<$'EOF'\nEOF\ngit tag v4\n$EOF",
            "cat <<-$'EOF'\n\tEOF\ngit tag v4\n$EOF",
            "cat <<E$'OF'\nEOF\ngit tag v4\nE$OF",
            "cat <<$'E\\x4fF'\nEOF\ngit tag v4\n$E\\x4fF",
            "cat <<E\n$'$(git tag v4)'\nE",
            "cat <<E\n$'x' `git tag v4`\nE",
            "cat <<E\n$$'$(git tag v4)'\nE",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in (
            "echo $$'\\' ; git tag v1 ; echo \"'\"",
            "echo $$$$'\\' ; git tag v1 ; echo \"'\"",
            "echo a$$'\\' ; git tag v1 ; echo \"'\"",
            "x=$$'\\'; git tag v1; echo \"'\"",
            "echo $$'\\'' ; git tag v1",
            'cat <<$"EOF"\nEOF\ngit tag v4\n$EOF',
            'cat <<$"EOF"\n$EOF\ngit tag v4\nEOF',
            "cat <<$$'EOF'\n$EOF\ngit tag v4\n$$EOF",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("bash and zsh", err)
            self.assertNotIn("Traceback", err)
        for command in ("echo $$'git tag v5'", "cat <<$'EOF'\ngit tag v6\nEOF", "echo $$ $'\\x41' $$$'\\x41'", "echo {a..c} {Z..a}"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

    def test_a_substitution_inside_double_quotes_is_read_in_its_own_context(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            """x="$(printf "%s" "a'b")"; git tag v1; y="$(printf "%s" "c'd")\"""",
            """echo "$(echo "'")"; git tag v2; echo "$(echo "'")\"""",
            """echo "`echo "'"`"; git tag v3; echo "`echo "'"`\"""",
            """echo "$(echo "'")" ; echo ' #' ; git tag v4""",
            """echo "$(echo "it's")"; {git,tag} v5""",
            """echo "$(echo '"')"; git tag v6; echo "$(echo '"')\"""",
            """echo "${x:-"'"}"; git tag v1; echo "${x:-"'"}\"""",
            """echo "$(echo ")" "'")"; git tag v1; echo "'\"""",
            """echo "$(echo "#" "'")"; git tag v1; echo "'\"""",
            """echo "$(echo 'a"b')"; git tag v1; echo '"'""",
            """echo "a$(echo "'")b" ; git tag v1 ; echo "'\"""",
            """echo "$( (echo "'") )"; git tag v1; echo "'\"""",
            """echo "$(case x in x) echo "'";; esac)"; git tag v1; echo "'\"""",
            """echo "$(echo "'" # )\n)"; git tag v1; echo "'\"""",
            """echo "`echo '"'`"; git tag v1; echo '"'""",
            """echo "${x:-$(echo "'")}"; git tag v1; echo "'\"""",
            """echo "${x:-`echo "'"`}"; git tag v1; echo "'\"""",
            """echo "${x:-${y:-"'"}}"; git tag v1; echo "'\"""",
            """echo "`echo \\`echo "'"\\``"; git tag v1; echo "'\"""",
            """echo "a\\\nb$(echo "'")"; git tag v1; echo "'\"""",
            """echo "$(echo "'" # "\n)"; git tag v1; echo "'\"""",
            """echo "$(cat <<'EOF'\n"\nEOF\n)"; git tag v1; echo '"'""",
            """echo "$(( 1 <<EOF\n))"; git tag v1\nEOF""",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        code, _, err = run_hook("deploy_gate.py", bash_event("""echo "${x:-'"'}"; git tag v1; echo "'\""""), self.root)
        self.assertEqual(code, 2)
        self.assertIn("bash and zsh", err)
        for command in ('echo "$(echo "git tag v7")"', """echo "$(echo "'")"; echo "git tag v8\"""", 'echo "${x:-git tag v9}"'):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)
        started = time.monotonic()
        code, _, err = run_hook("deploy_gate.py", bash_event('echo "' + '$((echo "' * 40 + "x" + '") )' * 40 + '"; git tag v1'), self.root)
        self.assertEqual(code, 2)
        self.assertLess(time.monotonic() - started, 5)

    def test_a_substitution_in_double_quotes_ends_where_the_shells_end_it(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            """git log --grep "$(echo case)"; git tag v1; echo "$(echo esac)\"""",
            """echo "$(echo case)"; git tag v1; echo "$(echo esac)\"""",
            """echo "$(cat <<<EOF\n)"; git tag v1; echo "x"\nEOF""",
            """echo "$(cat <<< EOF\n)"; git tag v1; echo "x"\nEOF""",
            """echo "$(cat <<<'EOF'\n)"; git tag v1; echo "x"\nEOF""",
            """echo "$(cat <<<"EOF"\n)"; git tag v1; echo "x"\nEOF""",
            """echo "$( ((1 <<EOF))\n)" "a"; git tag v1 # "\nEOF""",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in (
            """echo "$$(" ; git tag v1 ; echo ")\"""",
            """echo "$${x" ; git tag v1 ; echo "}\"""",
            """echo "$$$$(" ; git tag v1 ; echo ")\"""",
            """echo "${x:-$$(}" ; git tag v1 ; echo ")\"""",
            """echo "${x:-$${}" ; git tag v1 ; echo "}\"""",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("bash and zsh", err)
        for command in ('echo "$(echo hi', 'echo "${x:-$(echo hi', 'echo "`echo hi'):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("never closes", err)
        for command in ('echo "$(cat case.txt)"', 'echo "$$(echo hi)"', 'echo "$${HOME}"', 'echo "$$(git tag v1)"', 'cat <<<"$(echo x)"', "cat <<EOF\n$$(git tag v1)\nEOF"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)
        started = time.monotonic()
        code, _, err = run_hook("deploy_gate.py", bash_event('echo "' + "$$(" * 70_000 + ")" * 70_000 + '"; git tag v1'), self.root)
        self.assertEqual(code, 2)
        self.assertLess(time.monotonic() - started, 5)

    def test_the_gate_never_fails_open_on_a_long_or_nested_call(self):
        self.configure(gatedCommands=["^git tag ", "^git push .*--force"])
        refs = " ".join(f"r{n}" for n in range(70))
        code, _, err = run_hook("deploy_gate.py", bash_event(f"env git push origin {refs} --force"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("release authorisation", err)
        started = time.monotonic()
        code, _, err = run_hook("deploy_gate.py", bash_event("eval " * 40 + "git tag v1"), self.root)
        self.assertEqual(code, 2)
        self.assertLess(time.monotonic() - started, 5)
        code, _, err = run_hook("deploy_gate.py", bash_event("x " * 200000), self.root)
        self.assertEqual(code, 2)
        self.assertIn("too long to read", err)
        paths = " ".join(f"src/module_{n}/file_{n}.py" for n in range(5000))
        started = time.monotonic()
        self.assertEqual(run_hook("deploy_gate.py", bash_event(f"env git add {paths}"), self.root), (0, "", ""))
        self.assertLess(time.monotonic() - started, 5)
        self.configure(gatedCommands=["^npm publish|^gh release "])
        code, _, err = run_hook("deploy_gate.py", bash_event("X=1 gh release create v1"), self.root)
        self.assertEqual(code, 2)
        for pattern in ["(?i)^gh release ", r"\Agh release ", "^(?:npm publish|gh release )"]:
            self.configure(gatedCommands=[pattern])
            code, _, err = run_hook("deploy_gate.py", bash_event("sudo /usr/bin/gh release create v1"), self.root)
            self.assertEqual(code, 2, pattern)
        self.configure(gatedCommands=["^git tag "])
        code, _, err = run_hook("deploy_gate.py", bash_event("echo " + "$(" * 2000 + "git tag v1" + ")" * 2000), self.root)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)
        started = time.monotonic()
        code, _, err = run_hook("deploy_gate.py", bash_event("x" * 5_000_000 + " && git tag v1"), self.root)
        self.assertEqual(code, 2)
        self.assertLess(time.monotonic() - started, 5)
        started = time.monotonic()
        code, out, err = run_hook("deploy_gate.py", bash_event("x " * 99_000 + "&& git status"), self.root)
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertLess(time.monotonic() - started, 5)
        for command in (
            "SHELL=/bin/bash eval 'git tag v1'",
            'PAGER=/bin/sh eval "git tag v1"',
            "SHELL=/bin/bash command eval 'git tag v1'",
            "X=/bin/sh ionice -c 2 bash -c 'git tag v1'",
            "X=/bin/eval Y=\"'\" eval 'git tag v1'",
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
        for command in ("sh " * 20_000 + "-c 'git tag v1'", "x" * 999_000 + " && git tag v1", "'" + "x " * 450_000):
            started = time.monotonic()
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command[:20])
            self.assertLess(time.monotonic() - started, 5, command[:20])
        config = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entries = [hook for group in config["hooks"]["PreToolUse"] for hook in group["hooks"] if "deploy_gate.py" in hook["command"]]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get("onFailure"), "block")
        self.assertGreater(entries[0].get("timeout", 0), 0)

    def test_a_gated_command_is_caught_behind_a_prefix(self):
        self.configure(gatedCommands=["^git tag "])
        for command in (
            "X=1 git tag v1",
            "env git tag v2",
            "sudo -u ci git tag v3",
            "time git tag v4",
            "! git tag v5",
            "{ git tag v6; }",
            "if true; then git tag v7; fi",
            "git -C . tag v8",
            'echo "$(git tag v9)"',
            'bash --norc -c "git tag v10"',
            'bash -o pipefail -c "git tag v11"',
            "git status | git tag v12",
            'eval "git tag v13"',
        ):
            code, _, err = run_hook("deploy_gate.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("release authorisation", err)
        for command in ('echo "git tag v1"', 'git log --grep "git tag "', 'git commit -m "add git tag support"', "echo '$(git tag v1)'", "echo '`git tag v1`'", 'echo "\\$(git tag v1)"', "echo $'$(git tag v1)'"):
            self.assertEqual(run_hook("deploy_gate.py", bash_event(command), self.root), (0, "", ""), command)

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


    def test_a_commit_it_cannot_read_is_blocked(self):
        self.init_repo()
        self.configure()
        (self.root / "config.py").write_text("AWS_KEY = 'AKIAJ4QX7ZK2M9P3T6RQ'\n")
        self.git("add", "config.py")
        for command in ("git commit -m x; echo " + "{a,b}" * 14, "git commit -m x; echo $$'\\' ; echo \"'\""):
            code, _, err = run_hook("secret_guard.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("secret-guard", err)
            self.assertNotIn("Traceback", err)

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


    def test_a_commit_it_cannot_read_is_blocked(self):
        self.init_repo()
        self.configure()
        self.add_ticket("in-progress")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n")
        self.git("add", "src/a.py")
        command = "git commit -m x; echo " + "{a,b}" * 14
        code, _, err = run_hook("ticket_sync.py", bash_event(command), self.root)
        self.assertEqual(code, 2)
        self.assertIn("ticket-sync", err)
        self.assertNotIn("Traceback", err)
        self.add_ticket("done")
        self.assertEqual(run_hook("ticket_sync.py", bash_event(command), self.root), (0, "", ""))

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
            bash_event("cd .claude/worktrees/w1; git commit -am x"),
        ):
            code, _, err = run_hook("red_guard.py", event, self.root)
            self.assertEqual(code, 2, event)
            self.assertIn("worktree is red", err)

    def test_commits_in_another_repository_never_run_its_feedback_command(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(0))
        marker = self.root / "ran"
        foreign = self.root / "vendor" / "lib"
        foreign.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=foreign, check=True)
        (foreign / ".claude").mkdir()
        (foreign / ".claude" / "toolkit.json").write_text(json.dumps({"feedbackCommand": feedback(1, "foreign", marker=str(marker))}))
        (foreign / "app.py").write_text("x = 1\n")
        for event in (
            bash_event("cd vendor/lib && git commit -am x"),
            bash_event("git -C vendor/lib commit -am x"),
            {**bash_event("git commit -am x"), "cwd": str(foreign)},
        ):
            self.assertEqual(run_hook("red_guard.py", event, self.root), (0, "", ""), event)
        self.assertFalse(marker.exists())

    def test_reworded_commits_are_recognised(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"))
        (self.root / "app.py").write_text("x = 1\n")
        for command in (
            "git add -A;git commit -m x",
            "true&&git commit -m x",
            "(git commit -m x)",
            f"{shutil.which('git')} commit -m x",
            'git -c user.name="A B" commit -m x',
            f'git -C "{self.root}" commit -m x',
            'bash -c "git add -A && git commit -m x"',
            "eval 'git commit -m x'",
            "echo $'a\\'b'; git commit -am x; echo 'c'",
            "x=$'\\'' git commit -am x; echo \"'\"",
            "cat <<E'OF'\nEOF\ngit commit -am x\nE",
            "cat <<E:OF\nE:OF\ngit commit -am x\nE",
            "$'\\x67it' commit -am x",
            "git {commit,-am,x}",
            "echo $'\\c'; git commit -am x; echo 'x'",
            "echo {W..a..5}'x'; git commit -am x; echo 'y'",
            "cat <<$'EOF'\nEOF\ngit commit -am x\n$EOF",
            """x="$(printf "%s" "a'b")"; git commit -am x; y="$(printf "%s" "c'd")\"""",
            """echo "`echo '"'`"; git commit -am x; echo '"'""",
            """echo "${x:-"'"}"; git commit -am x; echo "'\"""",
            """echo "$(echo ")" "'")"; git commit -am x; echo "'\"""",
            """echo "$(cat <<'EOF'\n"\nEOF\n)"; git commit -am x; echo '"'""",
            """echo "$(cat case.txt)" && git commit -am x""",
            """echo "$(echo $case)"; git commit -am x""",
            """echo "$(echo case-x)"; git commit -am x""",
            """echo "$(x=case; echo $x)"; git commit -am x""",
            """echo "$(case case in case) echo a;; esac)"; git commit -am x""",
            """echo "$(cat <<<EOF\n)"; git commit -am x; echo "x"\nEOF""",
            """echo "$( echo $((1 <<EOF)) x\n)"; git commit -am x\nEOF""",
            """echo "$( for ((i=1<<EOF; i<0; i++)); do :; done\n)"; git commit -am x\nEOF""",
        ):
            code, _, err = run_hook("red_guard.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertIn("boom", err)
        code, _, err = run_hook("red_guard.py", bash_event("""echo "$$(" ; git commit -am x ; echo ")\""""), self.root)
        self.assertEqual(code, 2)
        self.assertIn("bash and zsh", err)
        code, _, err = run_hook("red_guard.py", bash_event("git commit -am " + "{a,b}" * 14), self.root)
        self.assertEqual(code, 2)
        self.assertIn("red-guard", err)
        self.assertNotIn("Traceback", err)
        for command in ("echo $$'\\' ; git commit -am x ; echo \"'\"", "echo " + "{a,b}" * 14):
            code, _, err = run_hook("red_guard.py", bash_event(command), self.root)
            self.assertEqual(code, 2, command)
            self.assertTrue(err.startswith("Blocked: red-guard could not read"), err)
            self.assertNotIn("Traceback", err)
        for command in ('echo "git commit"', "git log --grep commit", "git -c commit.gpgsign=false status"):
            self.assertEqual(run_hook("red_guard.py", bash_event(command), self.root), (0, "", ""), command)

    def test_a_command_that_can_change_files_before_its_commit_always_runs_the_check(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"), testGlobs=["tests/"])
        for command in ("echo 1 >> app.py && git commit -am x", "git commit --amend -m y", "git stash pop && git commit -am x"):
            self.assertEqual(run_hook("red_guard.py", bash_event(command), self.root)[0], 2, command)
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_x.py").write_text("assert False\n")
        for command in ("sed -i '' s/0/1/ app.py && git commit -am x", "cat README.md > app.py && git commit -am x", "git status\nsed -i '' s/0/1/ app.py\ngit commit -am x"):
            self.assertEqual(run_hook("red_guard.py", bash_event(command), self.root)[0], 2, command)
        for command in ("git add -A && git commit -m x", "cd . && git status && git -C . add tests && git commit -m x", "git add -A && git commit -m x 2>&1 | tail -5", "git commit -am x > /dev/null", "git add tests && git commit -F - <<'EOF'\ntest(x): reproduce (a bug)\nEOF"):
            self.assertEqual(run_hook("red_guard.py", bash_event(command), self.root), (0, "", ""), command)

    def test_an_unparsable_directory_falls_back_to_the_shell_directory(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"))
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event('cd "$PWD" && git commit -am x'), self.root)
        self.assertEqual(code, 2)
        self.assertIn("boom", err)

    def test_a_shift_in_arithmetic_does_not_hide_the_commit_after_it(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"))
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("echo $((1<<2))\ngit commit -am x"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("boom", err)

    def test_a_shell_option_before_c_does_not_hide_the_commit(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"))
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event('bash --norc -c "git commit -am x"'), self.root)
        self.assertEqual(code, 2)
        self.assertIn("boom", err)

    def test_an_option_after_c_does_not_hide_the_commit(self):
        self.init_repo()
        self.configure_committed(feedbackCommand=feedback(1, "boom"))
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("bash -c -- 'git commit -am x'"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("boom", err)

    def test_empty_test_globs_use_the_default_test_patterns(self):
        self.init_repo()
        marker = self.root / "ran"
        for config in ({"testGlobs": []}, {}):
            self.configure_committed(feedbackCommand=feedback(1, marker=str(marker)), **config)
            (self.root / "tests").mkdir(exist_ok=True)
            (self.root / "tests" / "test_bug.py").write_text("assert False\n")
            self.assertEqual(run_hook("red_guard.py", bash_event("git commit -m x"), self.root), (0, "", ""), config)
            self.assertFalse(marker.exists())

    def test_says_so_when_the_feedback_command_prints_nothing(self):
        self.init_repo()
        self.configure(feedbackCommand="exit 1")
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("No output.", err)
        self.assertNotIn("Last 0 lines", err)

    def test_feedback_past_the_limit_is_stopped_with_its_children(self):
        sys.path.insert(0, str(SCRIPTS))
        import red_guard

        started = time.monotonic()
        code, _ = red_guard.run_feedback("sleep 30 & echo $! > pid; wait", self.root, 1)
        self.assertLess(time.monotonic() - started, 5)
        self.assertIsNone(code)
        child = int((self.root / "pid").read_text())
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail(f"child {child} outlived the feedback command's limit")
        reason = red_guard.timeout_reason("make check", red_guard.LIMIT_SECONDS, "")
        self.assertIn("570 seconds", reason)
        self.assertIn("red", reason)

    def test_a_feedback_command_past_the_limit_blocks_the_commit(self):
        sys.path.insert(0, str(SCRIPTS))
        import red_guard

        self.init_repo()
        self.configure(feedbackCommand="make check")
        (self.root / "app.py").write_text("x = 1\n")
        stderr = io.StringIO()
        with mock.patch.object(red_guard, "run_feedback", return_value=(None, "")), mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.root)}), contextlib.redirect_stderr(stderr):
            code = red_guard.guard({**bash_event("git commit -m x"), "cwd": str(self.root)}, "git commit -m x")
        self.assertEqual(code, 2)
        self.assertIn("570 seconds", stderr.getvalue())

    def test_a_green_command_that_leaves_a_background_child_returns_at_once(self):
        sys.path.insert(0, str(SCRIPTS))
        import red_guard

        started = time.monotonic()
        code, output = red_guard.run_feedback("(sleep 30 & echo $! > pid); echo ok", self.root, 20)
        self.addCleanup(subprocess.run, ["kill", "-9", (self.root / "pid").read_text().strip()], capture_output=True)
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(code, 0)
        self.assertIn("ok", output)

    def test_hook_entry_fails_closed_and_outlasts_the_feedback_limit(self):
        sys.path.insert(0, str(SCRIPTS))
        import red_guard

        config = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entries = [hook for group in config["hooks"]["PreToolUse"] for hook in group["hooks"] if "red_guard.py" in hook["command"]]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.get("onFailure"), "block")
        self.assertNotIn("if", entry)
        self.assertGreater(entry.get("timeout", 0), red_guard.LIMIT_SECONDS)

    def test_a_fault_blocks_a_commit_readably_and_never_blocks_other_commands(self):
        self.init_repo()
        self.configure(feedbackCommand=123)
        (self.root / "app.py").write_text("x = 1\n")
        code, _, err = run_hook("red_guard.py", bash_event("git commit -m x"), self.root)
        self.assertEqual(code, 2)
        self.assertIn("red-guard", err)
        self.assertNotIn("Traceback", err)
        result = subprocess.run([sys.executable, str(SCRIPTS / "red_guard.py")], input="not json", capture_output=True, text=True, cwd=self.root, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

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
