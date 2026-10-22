"""PreToolUse hook for Bash.

On `git commit`, runs the project's feedback command and blocks the commit
while it is red, quoting the tail of its output. A commit never lands with the
project's own checks failing.

A commit whose pending changes are only workflow documents and test files skips
the check, so `fix-bug` can commit its failing regression test and a verifier
can record a reopen on a red tree.
"""

import os
import signal
import subprocess
import sys

from _common import block, commit_checkout, first_match, git, is_git_commit, load_config, read_event, tool_input

TAIL_LINES = 40
LIMIT_SECONDS = 570
WORKFLOW_FILES = ("GLOSSARY.md", "REVIEW.md")


def pending_paths(root):
    """Every path `git status` reports: staged, unstaged, untracked. Both sides of a rename. None when git fails.

    Read from the working tree, not the index, because in `git add -A && git commit` this hook runs before the add.
    """
    output = git(root, "status", "--porcelain", "-z", "--untracked-files=all")
    if output is None:
        return None
    fields = output.split("\0")
    paths = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            if index < len(fields) and fields[index]:
                paths.append(fields[index])
            index += 1
    return paths


def needs_check(paths, test_globs) -> bool:
    if paths is None:
        return True
    return any(not (path.startswith("docs/") or path in WORKFLOW_FILES or first_match(path, test_globs)) for path in paths)


def run_feedback(command: str, cwd, limit: float):
    """Run the feedback command through the shell. Returns the exit code, None past `limit` seconds, and the combined output.

    The command runs in its own process group so that, past the limit, its
    children die with it: a `sleep` or `node` left behind would hold the
    output pipe open and keep the hook waiting.
    """
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=limit)
        return process.returncode, output
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            output = ""
        return None, output or ""


def quoted_tail(output: str) -> str:
    tail = output.rstrip("\n").splitlines()[-TAIL_LINES:]
    return f"Last {len(tail)} {'line' if len(tail) == 1 else 'lines'} of output:\n" + "\n".join(tail) + "\n"


def red_reason(command: str, code: int, output: str) -> str:
    return (
        "Commit stopped: the feedback command is red.\n"
        f"Command: {command}\n"
        f"Exit code: {code}\n" + quoted_tail(output) + "Fix the code and commit again. Never edit a test to reach green."
    )


def timeout_reason(command: str, limit: float, output: str) -> str:
    return (
        f"Commit stopped: the feedback command did not finish within {limit} seconds, and a feedback command that cannot finish is treated as red.\n"
        f"Command: {command}\n" + quoted_tail(output) + "Find what hangs or makes it slow, fix it, and commit again."
    )


def main() -> int:
    try:
        event = read_event()
        command = tool_input(event).get("command") or ""
        if not is_git_commit(command):
            return 0
    except Exception:
        return 0
    try:
        return guard(event, command)
    except Exception as exc:
        return block(f"Commit stopped: red-guard could not check the commit ({type(exc).__name__}: {exc}). Fix the cause, often `feedbackCommand` in .claude/toolkit.json, and commit again.")


def guard(event: dict, command: str) -> int:
    root = commit_checkout(event, command)
    config = load_config(root)
    if config is None:
        return 0
    feedback = config.get("feedbackCommand")
    if not feedback:
        return 0
    if not needs_check(pending_paths(root), config.get("testGlobs") or []):
        return 0
    code, output = run_feedback(feedback, root, LIMIT_SECONDS)
    if code is None:
        return block(timeout_reason(feedback, LIMIT_SECONDS, output))
    if code == 0:
        return 0
    return block(red_reason(feedback, code, output))


if __name__ == "__main__":
    sys.exit(main())
