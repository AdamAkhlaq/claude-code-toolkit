"""PreToolUse hook for Bash.

On `git commit`, runs the project's feedback command and blocks the commit
while it is red, quoting the tail of its output. A commit never lands with the
project's own checks failing.
"""

import subprocess
import sys

from _common import block, is_git_commit, load_config, project_dir, read_event, tool_input

TAIL_LINES = 40


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
        f"Last {len(tail)} lines of output:\n" + "\n".join(tail) + "\n"
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
    code, output = run_feedback(feedback, root)
    if code == 0:
        return 0
    return block(red_reason(feedback, code, output))


if __name__ == "__main__":
    sys.exit(main())
