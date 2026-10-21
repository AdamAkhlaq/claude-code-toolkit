"""PreToolUse hook for Bash.

Blocks any command matching a pattern in `gatedCommands` unless a human has
authorised a release, either by exporting RELEASE_AUTHORIZED or by creating
`.claude/.release-authorized`.
"""

import os
import re
import sys

from _common import block, load_config, project_dir, read_event, tool_input

MARKER_RELPATH = ".claude/.release-authorized"


def authorised(root) -> bool:
    if os.environ.get("RELEASE_AUTHORIZED", "").strip():
        return True
    return (root / MARKER_RELPATH).exists()


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    patterns = [p for p in config.get("gatedCommands") or [] if isinstance(p, str) and p]
    if not patterns:
        return 0
    command = tool_input(read_event()).get("command") or ""
    if not command:
        return 0
    for pattern in patterns:
        try:
            matched = re.search(pattern, command)
        except re.error:
            print(f"toolkit: invalid regex in gatedCommands: {pattern!r}", file=sys.stderr)
            continue
        if not matched:
            continue
        if authorised(root):
            return 0
        shown = command if len(command) <= 120 else command[:117] + "..."
        return block(
            f"Blocked: '{shown}' matches gated command pattern '{pattern}' in .claude/toolkit.json. "
            "This is a one-way door and needs release authorisation from a human. "
            f"After approving, they export RELEASE_AUTHORIZED=1 for the session or create {MARKER_RELPATH}. "
            "Prepare everything up to this step and stop."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
