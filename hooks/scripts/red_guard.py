"""PreToolUse hook for Bash.

On `git commit`, runs the project's feedback command and blocks the commit
while it is red, quoting the tail of its output. A commit never lands with the
project's own checks failing.

A commit whose pending changes are only workflow documents and test files skips
the check, so `fix-bug` can commit its failing regression test and a verifier
can record a reopen on a red tree.
"""

import subprocess
import sys

from _common import block, first_match, git, is_git_commit, load_config, project_dir, read_event, tool_input

TAIL_LINES = 40
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


def run_feedback(command: str, cwd):
    """Run the feedback command through the shell. Returns the exit code and the combined output."""
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
    )
    return result.returncode, result.stdout


def red_reason(command: str, code: int, output: str) -> str:
    tail = output.rstrip("\n").splitlines()[-TAIL_LINES:]
    return (
        "Commit stopped: the feedback command is red.\n"
        f"Command: {command}\n"
        f"Exit code: {code}\n"
        f"Last {len(tail)} {'line' if len(tail) == 1 else 'lines'} of output:\n" + "\n".join(tail) + "\n"
        "Fix the code and commit again. Never edit a test to reach green."
    )


def main() -> int:
    command = tool_input(read_event()).get("command") or ""
    if not is_git_commit(command):
        return 0
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    feedback = config.get("feedbackCommand")
    if not feedback:
        return 0
    if not needs_check(pending_paths(root), config.get("testGlobs") or []):
        return 0
    code, output = run_feedback(feedback, root)
    if code == 0:
        return 0
    return block(red_reason(feedback, code, output))


if __name__ == "__main__":
    sys.exit(main())
