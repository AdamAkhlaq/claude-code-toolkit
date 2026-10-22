"""PreToolUse hook for Bash.

On `git commit`, while a ticket is in progress, asks for confirmation when
source files are staged but nothing under that change's folder is. Keeps the
ticket graph in step with the code it describes.
"""

import re
import sys
from pathlib import Path

from _common import ask, commits_all_tracked, git, is_git_commit, load_config, project_dir, read_event, tool_input

CHANGES_RELPATH = "docs/changes"
STATUS_LINE = re.compile(r"^status:\s*['\"]?([A-Za-z-]+)", re.MULTILINE)


def in_progress_changes(root: Path):
    changes = root / CHANGES_RELPATH
    if not changes.is_dir():
        return []
    found = []
    for ticket in sorted(changes.glob("*/tickets/*.md")):
        try:
            head = ticket.read_text(encoding="utf-8")[:2000]
        except OSError:
            continue
        match = STATUS_LINE.search(head)
        if match and match.group(1) == "in-progress":
            change_dir = ticket.parent.parent
            if change_dir not in found:
                found.append(change_dir)
    return found


def staged_files(root: Path, include_unstaged: bool):
    args = ["diff", "--name-only"]
    args.append("HEAD" if include_unstaged else "--cached")
    output = git(root, *args)
    return [line.strip() for line in (output or "").splitlines() if line.strip()]


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    command = tool_input(read_event()).get("command") or ""
    if not is_git_commit(command):
        return 0
    active = in_progress_changes(root)
    if not active:
        return 0
    files = staged_files(root, commits_all_tracked(command))
    if not files:
        return 0
    source = [f for f in files if not f.startswith("docs/")]
    if not source:
        return 0
    stale = []
    for change_dir in active:
        prefix = change_dir.relative_to(root).as_posix() + "/"
        if not any(f.startswith(prefix) for f in files):
            stale.append(change_dir.name)
    if not stale:
        return 0
    names = ", ".join(stale)
    return ask(
        "PreToolUse",
        f"Source files are staged but nothing under docs/changes/{names}/ is, and that change has a ticket in progress. "
        "Normally the ticket's status or evidence is updated in the same commit. "
        "Confirm to commit anyway, or stage the ticket update first.",
    )


if __name__ == "__main__":
    sys.exit(main())
