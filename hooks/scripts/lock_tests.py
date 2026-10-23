"""PreToolUse hook for Edit, Write and MultiEdit.

While `.claude/.tests-locked` exists, blocks edits to test files. The `fix-bug`
skill creates the marker after committing a failing test, so the fix cannot
make the test pass by changing the test.
"""

import sys

from _common import DEFAULT_TEST_GLOBS, block, first_match, load_config, project_dir, read_event, target_path

LOCK_RELPATH = ".claude/.tests-locked"


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    if not (root / LOCK_RELPATH).exists():
        return 0
    rel = target_path(read_event(), root)
    if not rel:
        return 0
    globs = config.get("testGlobs") or DEFAULT_TEST_GLOBS
    hit = first_match(rel, globs)
    if not hit:
        return 0
    return block(
        f"Blocked: '{rel}' is a test file (matches '{hit}') and tests are locked while a bug fix is in progress "
        f"({LOCK_RELPATH} exists). Change the code until the existing test passes. "
        f"If the test itself is wrong, say so and ask the user to unlock with: rm {LOCK_RELPATH}"
    )


if __name__ == "__main__":
    sys.exit(main())
