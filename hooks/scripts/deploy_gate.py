"""PreToolUse hook for Bash.

Blocks any command matching a pattern in `gatedCommands` unless a human has
authorised a release, either by exporting RELEASE_AUTHORIZED or by creating
`.claude/.release-authorized`. Each pattern is matched against the whole
command and against each simple command in it, anchored at every word that
could name a program, so `^git tag ` also catches `cd . && git tag v1` and
`sudo git tag v1`. A call too long or too deeply nested to read is blocked
rather than half read, as is one bash and zsh read differently, one holding
a double-quoted substitution that never closes, and one holding a `case`
form inside a substitution that the reader does not model.
A script fed to an interpreter, such as `echo 'git tag v1' | bash`, is not
read, nor is a word built from a variable, such as `git $t v1`.
"""

import os
import re
import sys

from _common import BRACES, SHELLS, ShellsDiffer, Unclosed, Unmodelled, Unreadable, block, closing_paren, dollar_run, git_options, is_operator, load_config, project_dir, read_event, shell_script, shell_source, shell_tokens, tool_input

MARKER_RELPATH = ".claude/.release-authorized"


def authorised(root) -> bool:
    if os.environ.get("RELEASE_AUTHORIZED", "").strip():
        return True
    return (root / MARKER_RELPATH).exists()


BUDGET = 100_000
# shlex builds a word one character at a time, so reading a word costs the square of its length: 300,000 characters is read in under a second.
CHARACTERS = 300_000


def readings(command: str, budget=None, seen=None) -> list:
    """Each simple command in `command` as a line of its words, with the offset in the line where each word that could name a program starts, by basename.

    A pattern anchored with `^` is matched at every one of those offsets, so
    `^git tag ` catches `X=1 git tag`, `sudo /usr/bin/git tag` and `then git
    tag` alike, and the line stays whole however long it is, in one string per
    simple command. A word holding whitespace came from quotes and names no
    program, which keeps `echo "git tag v1"` silent. `git` is read past its
    global options as well, and the scripts of `eval`, `bash -c`, `$(...)` and
    backticks are read as commands of their own, inside double quotes and in
    the body of a heredoc with an unquoted delimiter too. Every `eval` or shell word is read into, since
    an earlier one may be an assignment's value or a wrapper's argument, such
    as `SHELL=/bin/bash eval '...'`, and a script already read in the call is
    not read again. Every word read or scanned counts against BUDGET and every
    character against CHARACTERS, charged before it is parsed, and past either
    the call is Unreadable.
    """
    budget = [BUDGET, CHARACTERS] if budget is None else budget
    seen = set() if seen is None else seen
    spend(budget, 0, len(command))
    found = []
    bodies = []
    spans = []
    inners = substitutions(shell_source(command, bodies, spans)) + spans
    for body in bodies:
        inners.extend(substitutions(body, quotes=False))
    for inner in inners:
        found.extend(read_once(inner, budget, seen))
    for words in simple_commands(command):
        spend(budget, len(words), 0)
        line = " ".join(words)
        starts = []
        offset = 0
        for index, word in enumerate(words):
            end = offset + len(word) + 1
            if word and not word.startswith("-") and not any(char.isspace() for char in word):
                name = os.path.basename(word)
                starts.append(offset + len(word) - len(name))
                if name == "git":
                    after = git_options(words[index + 1 :])[1]
                    spend(budget, len(after), sum(map(len, after)))
                    found.append((" ".join(["git", *after]), [0]))
                elif name == "eval":
                    spend(budget, 0, len(line) - end + 1)
                    found.extend(read_once(line[end:], budget, seen))
                elif name in SHELLS:
                    spend(budget, len(words) - index, 0)
                    script = shell_script(words[index + 1 :])
                    if script is not None:
                        found.extend(read_once(script, budget, seen))
            offset = end
        found.append((line, starts))
    return found


def read_once(script: str, budget: list, seen: set) -> list:
    if script in seen:
        return []
    seen.add(script)
    return readings(script, budget, seen)


def spend(budget: list, words: int, characters: int) -> None:
    budget[0] -= words
    budget[1] -= characters
    if budget[0] < 0 or budget[1] < 0:
        raise Unreadable


def matches(pattern: str, command: str, lines: list) -> bool:
    """True when `pattern` matches the raw command, or any line, or, with its anchors taken out, any line at a program word.

    Taking every anchor out, not only a leading one, lets each alternative of
    `^npm publish|^gh release ` start at a program word. It only widens where
    the pattern may start, so the gate errs toward blocking.
    """
    whole = re.compile(pattern)
    bare = without_anchors(pattern)
    anchored = re.compile(bare) if bare != pattern else None
    if whole.search(command):
        return True
    for line, starts in lines:
        if whole.search(line) or (anchored and any(anchored.match(line, start) for start in starts)):
            return True
    return False


def without_anchors(pattern: str) -> str:
    """`pattern` without each `^` or `\\A` that anchors, leaving an escaped `\\^` and a `^` inside `[...]`."""
    kept = []
    in_class = False
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            if in_class or pattern[index + 1 : index + 2] != "A":
                kept.append(pattern[index : index + 2])
            index += 2
            continue
        if in_class:
            if char == "]" and not (kept[-1] == "[" or kept[-1:] == ["^"] and kept[-2:-1] == ["["]):
                in_class = False
        elif char == "[":
            in_class = True
        elif char == "^":
            index += 1
            continue
        kept.append(char)
        index += 1
    return "".join(kept)


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
    """The command inside each `$(...)` and backtick span the shell runs in `command`, outside quotes and never after a backslash.

    `command` is `shell_source`'s text, which has already read each
    substitution inside double quotes into its spans and left only literal
    text there. With `quotes` false, as in a heredoc body, quote characters
    are literal. A run of `$` is read whole, so after `$$`, the PID, a `(` is
    literal. A backtick span ends at the first backtick not escaped, and its
    inner text is read with `\\``, `\\$` and `\\\\` unescaped, as bash does, so a
    nested backtick span is found when that text is read.
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
        elif quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif command.startswith("$$", index):
            end = dollar_run(command, index)
            index = end - 1 if (end - index) % 2 else end
            continue
        elif command.startswith("$(", index):
            end = closing_paren(command, index + 1)
            found.append(command[index + 2 : end])
            index = end
        elif char == "`":
            end = index + 1
            while end < len(command) and command[end] != "`":
                end += 2 if command[end] == "\\" else 1
            end = min(end, len(command))
            found.append(re.sub(r"\\([\\`$])", r"\1", command[index + 1 : end]))
            index = end
        index += 1
    return found


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
    except ShellsDiffer as exc:
        if authorised(root):
            return 0
        return block(f"Blocked: {exc}, so deploy-gate cannot tell whether this Bash call runs a gated command. Rephrase it so both shells read it alike.")
    except Unclosed as exc:
        if authorised(root):
            return 0
        return block(f"Blocked: {exc}, so deploy-gate cannot tell where it ends or whether this Bash call runs a gated command. Close it or split the call.")
    except Unmodelled as exc:
        if authorised(root):
            return 0
        return block(f"Blocked: deploy-gate does not read {exc}, so it cannot tell where the substitution ends or whether this Bash call runs a gated command. Rephrase it or split the call.")
    except (Unreadable, RecursionError):
        if authorised(root):
            return 0
        return block(
            f"Blocked: this Bash call is too long to read for gated commands (over {BUDGET} words or {CHARACTERS} characters, braces that expand past {BRACES} words, or nested too deep), "
            "so deploy-gate cannot tell whether it runs one. Split it into shorter calls."
        )
    except Exception as exc:
        if authorised(root):
            return 0
        return block(f"Blocked: deploy-gate could not read this Bash call ({type(exc).__name__}: {exc}), so it cannot tell whether it runs a gated command. Rephrase or split it.")
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
