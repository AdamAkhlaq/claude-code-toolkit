"""Shared helpers for the toolkit hooks. Standard library only.

Every hook follows the same contract: read the tool event from stdin, load
`.claude/toolkit.json` from the project, and exit 0 without output when the
config is absent. A hook only ever acts on a project that opted in.
"""

import fnmatch
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG_RELPATH = Path(".claude") / "toolkit.json"


def project_dir() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root) if root else Path.cwd()


def load_config(root: Path):
    path = root / CONFIG_RELPATH
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"toolkit: could not read {path}: {exc}", file=sys.stderr)
        return None
    return config if isinstance(config, dict) else None


def read_event() -> dict:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return {}
    return event if isinstance(event, dict) else {}


def tool_input(event: dict) -> dict:
    value = event.get("tool_input")
    return value if isinstance(value, dict) else {}


def target_path(event: dict, root: Path):
    """The project-relative POSIX path a file tool is about to touch, or None."""
    raw = tool_input(event).get("file_path")
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def first_match(rel: str, patterns):
    """The first pattern that matches, or None.

    A pattern ending in `/` matches that directory and everything beneath it.
    Any other pattern is a glob matched against the full relative path. A
    pattern with no `/` other than a trailing one (`.env`, `*.lock`,
    `__tests__/`) matches anywhere in the tree, not only at the root.
    """
    name = rel.rsplit("/", 1)[-1]
    for pattern in patterns or []:
        if not isinstance(pattern, str) or not pattern:
            continue
        if pattern.endswith("/"):
            folder = pattern[:-1]
            if rel == folder or rel.startswith(pattern):
                return pattern
            if "/" not in folder and f"/{pattern}" in f"/{rel}":
                return pattern
            continue
        if fnmatch.fnmatchcase(rel, pattern):
            return pattern
        if "/" not in pattern and fnmatch.fnmatchcase(name, pattern):
            return pattern
    return None


def block(reason: str) -> int:
    """Stop the tool call. Exit code 2 hands `reason` back to Claude."""
    print(reason, file=sys.stderr)
    return 2


def ask(event_name: str, reason: str) -> int:
    """Let the tool call through only if the user confirms it."""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload))
    return 0


def git(root: Path, *args: str):
    """Run git in the project. Returns stdout, or None when git fails."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def is_git_commit(command: str) -> bool:
    """True for `git commit`, allowing global options such as `git -C dir commit`."""
    tokens = command.split()
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        rest = tokens[index + 1 :]
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            if flag in ("-C", "-c", "--git-dir", "--work-tree") and rest:
                rest.pop(0)
        if rest and rest[0] == "commit":
            return True
    return False


def commit_checkout(event: dict, command: str) -> Path:
    """The top level of the checkout a `git commit` in `command` lands in.

    Starts from the event's `cwd`, the shell's real directory, falling back to
    the project directory; then applies a leading `cd <dir> &&` and any
    `git -C <dir>` on the commit. Inside a worktree this differs from
    `CLAUDE_PROJECT_DIR`, which always names the main checkout.
    """
    directory = Path(event.get("cwd") or project_dir())
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    if len(tokens) >= 3 and tokens[0] == "cd" and tokens[2] == "&&":
        directory = directory / os.path.expanduser(tokens[1])
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        rest = tokens[index + 1 :]
        dirs = []
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            if flag in ("-C", "-c", "--git-dir", "--work-tree") and rest:
                value = rest.pop(0)
                if flag == "-C":
                    dirs.append(value)
        if rest and rest[0] == "commit":
            for value in dirs:
                directory = directory / os.path.expanduser(value)
            break
    top = git(directory, "rev-parse", "--show-toplevel")
    return Path(top.strip()) if top else directory


def commits_all_tracked(command: str) -> bool:
    tokens = command.split()
    return any(token in ("-a", "--all") or (token.startswith("-") and not token.startswith("--") and "a" in token[1:]) for token in tokens)
