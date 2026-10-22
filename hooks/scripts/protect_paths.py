"""PreToolUse hook for Edit, Write and MultiEdit.

Blocks edits to any path listed under `protectedPaths` in `.claude/toolkit.json`.
"""

import sys

from _common import block, first_match, load_config, project_dir, read_event, target_path


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    patterns = config.get("protectedPaths") or []
    if not patterns:
        return 0
    rel = target_path(read_event(), root)
    if not rel:
        return 0
    hit = first_match(rel, patterns)
    if not hit:
        return 0
    return block(
        f"Blocked: '{rel}' is protected. It matches '{hit}' in .claude/toolkit.json protectedPaths. "
        "Protected paths are changed by a human, or by removing the entry when the protection no longer applies. "
        "Explain what change is needed and why instead of making it."
    )


if __name__ == "__main__":
    sys.exit(main())
