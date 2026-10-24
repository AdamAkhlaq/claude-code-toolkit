"""PreToolUse hook for Bash.

Blocks any command matching a pattern in `gatedCommands` unless a human has
authorised a release, either by exporting RELEASE_AUTHORIZED or by creating
`.claude/.release-authorized`. Each pattern is matched against the whole
command and against a line from each word that could name a program, so
`^git tag ` also catches `cd . && git tag v1` and `sudo git tag v1`. A script
fed to an interpreter, such as `echo 'git tag v1' | bash`, is not read.
"""

import os
import re
import sys

from _common import SHELLS, block, git_options, is_operator, load_config, project_dir, read_event, shell_script, shell_source, shell_tokens, tool_input

MARKER_RELPATH = ".claude/.release-authorized"


def authorised(root) -> bool:
    if os.environ.get("RELEASE_AUTHORIZED", "").strip():
        return True
    return (root / MARKER_RELPATH).exists()


WINDOW = 64


def program_lines(command: str) -> list:
    """The lines the patterns are matched against, one from each word of each simple command in `command` that could name a program.

    A line is the program's basename and the words after it, so `^git tag `
    catches `X=1 git tag`, `sudo git tag` and `then git tag` alike. A word
    holding whitespace came from quotes and names no program, which keeps
    `echo "git tag v1"` silent. A line from a simple command's first word
    is whole; one from a later word stops after WINDOW words, so a long
    argument list cannot make the lines grow with its square. `git` is read
    past its global options as well, and the scripts of `bash -c`, `eval`,
    `$(...)` and backticks are read as commands of their own, in the body of
    a heredoc with an unquoted delimiter too.
    """
    lines = []
    bodies = []
    inners = substitutions(shell_source(command, bodies))
    for body in bodies:
        inners.extend(substitutions(body, quotes=False))
    for inner in inners:
        lines.extend(program_lines(inner))
    for words in simple_commands(command):
        for index, word in enumerate(words):
            if not word or word.startswith("-") or any(char.isspace() for char in word):
                continue
            name = os.path.basename(word)
            rest = words[index + 1 :] if index == 0 else words[index + 1 : index + 1 + WINDOW]
            lines.append(" ".join([name, *rest]))
            if name == "git":
                lines.append(" ".join(["git", *git_options(rest)[1]]))
            elif name == "eval":
                lines.extend(program_lines(" ".join(words[index + 1 :])))
            elif name in SHELLS and (script := shell_script(words[index + 1 :])) is not None:
                lines.extend(program_lines(script))
    return lines


def simple_commands(command: str) -> list:
    """The words of each simple command in `command`, its redirections dropped."""
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
                found.append(words)
            words = []
    return found


def substitutions(command: str, quotes: bool = True) -> list:
    """The command inside each `$(...)` and backtick span the shell runs in `command`: outside quotes or inside double quotes, never inside single quotes or after a backslash.

    With `quotes` false, as in a heredoc body, quote characters are literal.
    """
    found = []
    quote = ""
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if not quotes and char in "'\"":
            pass
        elif quote in ("'", "$'"):
            if char == "'":
                quote = ""
        elif command.startswith("$'", index) and not quote:
            quote = "$'"
            index += 1
        elif char == "'" and not quote:
            quote = "'"
        elif char == '"':
            quote = "" if quote else '"'
        elif command.startswith("$(", index):
            end = closing_paren(command, index + 1)
            found.append(command[index + 2 : end])
            index = end
        elif char == "`":
            end = command.find("`", index + 1)
            end = len(command) if end == -1 else end
            found.append(command[index + 1 : end])
            index = end
        index += 1
    return found


def closing_paren(command: str, start: int) -> int:
    """The index of the `)` that closes the `(` at `start`, or the end of `command`.

    Parentheses in quoted text or after a backslash do not count, nor does the
    `)` that ends a `case` pattern.
    """
    depth = 0
    cases = []
    quote = ""
    index = start
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif keyword_at(command, index, "case"):
            cases.append(depth)
        elif keyword_at(command, index, "esac") and cases:
            cases.pop()
        elif char == "(":
            depth += 1
        elif char == ")" and not (cases and cases[-1] == depth):
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(command)


def keyword_at(command: str, index: int, word: str) -> bool:
    before = command[index - 1] if index else " "
    after = command[index + len(word) : index + len(word) + 1] or " "
    return command.startswith(word, index) and not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_")


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
    candidates = [command, *program_lines(command)]
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
