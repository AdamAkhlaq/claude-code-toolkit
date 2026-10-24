"""PreToolUse hook for Bash.

Blocks any command matching a pattern in `gatedCommands` unless a human has
authorised a release, either by exporting RELEASE_AUTHORIZED or by creating
`.claude/.release-authorized`. Each pattern is matched against the whole
command and against each simple command in it, so `^git tag ` also catches
`cd . && git tag v1`.
"""

import os
import re
import sys

from _common import SHELLS, block, is_operator, load_config, project_dir, read_event, shell_tokens, tool_input

MARKER_RELPATH = ".claude/.release-authorized"


def authorised(root) -> bool:
    if os.environ.get("RELEASE_AUTHORIZED", "").strip():
        return True
    return (root / MARKER_RELPATH).exists()


def simple_commands(command: str) -> list:
    """Each simple command in `command` as a line of words, its program named by basename and its redirections dropped.

    The script of `bash -c` or `eval` is split into its own simple commands.
    """
    found = []
    words = []
    redirect_target = False
    for token in [*shell_tokens(command), ";"]:
        if redirect_target:
            redirect_target = False
        elif not is_operator(token):
            words.append(token)
        elif "(" not in token and ("<" in token or ">" in token):
            redirect_target = True
        else:
            if words:
                found.extend(expand(words))
            words = []
    return found


def expand(words: list) -> list:
    program = os.path.basename(words[0])
    rest = words[1:]
    if program == "eval":
        return [" ".join([program, *rest]), *simple_commands(" ".join(rest))]
    if program in SHELLS:
        flags = list(rest)
        while flags and flags[0].startswith("-") and not flags[0].startswith("--"):
            flag = flags.pop(0)
            if "c" in flag[1:] and flags:
                return [" ".join([program, *rest]), *simple_commands(flags[0])]
    return [" ".join([program, *rest])]


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
    candidates = [command, *simple_commands(command)]
    for pattern in patterns:
        try:
            matched = any(re.search(pattern, candidate) for candidate in candidates)
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
