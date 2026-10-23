"""PreToolUse hook for Bash.

On `git commit`, runs the project's feedback command and blocks the commit
while it is red, quoting the tail of its output. A commit never lands with the
project's own checks failing.

A commit whose pending changes are only workflow documents and test files skips
the check, so `fix-bug` can commit its failing regression test and a verifier
can record a reopen on a red tree, as long as nothing else in the command can
change a file first. Only the project's own checkouts are checked: a commit in
another repository never runs that repository's command.
"""

import os
import signal
import subprocess
import sys
import tempfile

from _common import DEFAULT_TEST_GLOBS, block, commit_checkout, first_match, git, git_options, is_git_commit, is_operator, load_config, project_dir, read_event, same_repository, shell_tokens, tool_input

TAIL_LINES = 40
LIMIT_SECONDS = 570
WORKFLOW_FILES = ("GLOSSARY.md", "REVIEW.md")
BOOKKEEPING = ("add", "rm", "mv", "status", "diff", "log", "show", "commit")
READ_ONLY = ("cat", "grep", "head", "tail", "wc")


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


def only_bookkeeping(command: str) -> bool:
    """True when every simple command in `command` is a `cd`, a git command that cannot change the working tree, or a read-only filter, and nothing is redirected into a file.

    Only then does `git status`, read before the command runs, show everything
    the commit can contain: in `echo x >> app.py && git commit -am x` the
    source change does not exist yet when this hook runs.
    """
    tokens = shell_tokens(command)
    segments = [[]]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not is_operator(token):
            segments[-1].append(token)
        elif "<" in token or ">" in token:
            target = tokens[index] if index < len(tokens) else ""
            index += 1
            if ">" in token and not token.endswith("&") and target != "/dev/null":
                return False
        else:
            segments.append([])
    for words in segments:
        if not words or words[0] == "cd" or words[0] in READ_ONLY:
            continue
        if os.path.basename(words[0]) != "git":
            return False
        _, rest = git_options(words[1:])
        if not rest or rest[0] not in BOOKKEEPING:
            return False
    return True


def needs_check(paths, test_globs) -> bool:
    if not paths:
        return True
    return any(not (path.startswith("docs/") or path in WORKFLOW_FILES or first_match(path, test_globs)) for path in paths)


def run_feedback(command: str, cwd, limit: float):
    """Run the feedback command through the shell. Returns the exit code, None past `limit` seconds, and the combined output.

    Output goes to a file, not a pipe, and the hook waits for the command
    itself: a background child that a green command leaves running would hold
    a pipe open and keep the hook waiting until the limit. The command runs in
    its own process group so that, past the limit, its children die with it.
    """
    with tempfile.TemporaryFile() as sink:
        process = subprocess.Popen(command, shell=True, cwd=cwd, stdout=sink, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            code = None
        sink.seek(0)
        return code, sink.read().decode(errors="replace")


def quoted_tail(output: str) -> str:
    tail = output.rstrip("\n").splitlines()[-TAIL_LINES:]
    if not tail:
        return "No output.\n"
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
    if not same_repository(root, project_dir()):
        return 0
    config = load_config(root)
    if config is None:
        return 0
    feedback = config.get("feedbackCommand")
    if not feedback:
        return 0
    if only_bookkeeping(command) and not needs_check(pending_paths(root), config.get("testGlobs") or DEFAULT_TEST_GLOBS):
        return 0
    code, output = run_feedback(feedback, root, LIMIT_SECONDS)
    if code is None:
        return block(timeout_reason(feedback, LIMIT_SECONDS, output))
    if code == 0:
        return 0
    return block(red_reason(feedback, code, output))


if __name__ == "__main__":
    sys.exit(main())
