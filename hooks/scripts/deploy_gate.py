"""PreToolUse hook for Bash.

Blocks any command matching a pattern in `gatedCommands` unless a human has
authorised a release, either by exporting RELEASE_AUTHORIZED or by creating
`.claude/.release-authorized`. Each pattern is matched against the whole
command and against each simple command in it, anchored at every word that
could name a program, so `^git tag ` also catches `cd . && git tag v1` and
`sudo git tag v1`. A call too long to read is blocked rather than half read.
A script fed to an interpreter, such as `echo 'git tag v1' | bash`, is not
read.
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


BUDGET = 100_000


class Unreadable(Exception):
    """The call holds more words than the gate reads: it is blocked rather than half read."""


def readings(command: str, budget=None) -> list:
    """Each simple command in `command` as a line of its words, with the offset in the line where each word that could name a program starts, by basename.

    A pattern anchored with `^` is matched at every one of those offsets, so
    `^git tag ` catches `X=1 git tag`, `sudo /usr/bin/git tag` and `then git
    tag` alike, and the line stays whole however long it is, in one string per
    simple command. A word holding whitespace came from quotes and names no
    program, which keeps `echo "git tag v1"` silent. `git` is read past its
    global options as well, and the scripts of `eval`, `bash -c`, `$(...)` and
    backticks are read as commands of their own, in the body of a heredoc with
    an unquoted delimiter too. The first `eval` or shell in a simple command
    is read into once, and that reading meets any later one, so nesting costs
    no more than its length. Every word read counts against BUDGET, and past
    it the call is Unreadable.
    """
    budget = [BUDGET] if budget is None else budget
    found = []
    bodies = []
    inners = substitutions(shell_source(command, bodies))
    for body in bodies:
        inners.extend(substitutions(body, quotes=False))
    for inner in inners:
        found.extend(readings(inner, budget))
    for words in simple_commands(command):
        spend(budget, len(words))
        starts = []
        offset = 0
        read_into = False
        for index, word in enumerate(words):
            if word and not word.startswith("-") and not any(char.isspace() for char in word):
                name = os.path.basename(word)
                starts.append(offset + len(word) - len(name))
                rest = words[index + 1 :]
                if name == "git":
                    after = git_options(rest)[1]
                    spend(budget, len(after))
                    found.append((" ".join(["git", *after]), [0]))
                elif not read_into and (name == "eval" or name in SHELLS):
                    read_into = True
                    script = " ".join(rest) if name == "eval" else shell_script(rest)
                    if script is not None:
                        found.extend(readings(script, budget))
            offset += len(word) + 1
        found.append((" ".join(words), starts))
    return found


def spend(budget: list, words: int) -> None:
    budget[0] -= words
    if budget[0] < 0:
        raise Unreadable


def matches(pattern: str, command: str, lines: list) -> bool:
    """True when `pattern` matches the raw command, or any line, or, anchored with `^`, any line at a program word."""
    whole = re.compile(pattern)
    anchored = re.compile(pattern[1:]) if pattern.startswith("^") else None
    if whole.search(command):
        return True
    for line, starts in lines:
        if whole.search(line) or (anchored and any(anchored.match(line, start) for start in starts)):
            return True
    return False


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
    try:
        lines = readings(command)
    except Unreadable:
        if authorised(root):
            return 0
        return block(
            f"Blocked: this Bash call is too long to read for gated commands (over {BUDGET} words), so deploy-gate cannot tell whether it runs one. "
            "Split it into shorter calls."
        )
    for pattern in patterns:
        try:
            matched = matches(pattern, command, lines)
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
