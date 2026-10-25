"""Shared helpers for the toolkit hooks. Standard library only.

Every hook follows the same contract: read the tool event from stdin, load
`.claude/toolkit.json` from the project, and exit 0 without output when the
config is absent. A hook only ever acts on a project that opted in.
"""

import bisect
import fnmatch
import functools
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG_RELPATH = Path(".claude") / "toolkit.json"

DEFAULT_TEST_GLOBS = [
    "*.test.*",
    "*.spec.*",
    "*_test.*",
    "test_*",
    "tests/",
    "test/",
    "__tests__/",
    "spec/",
]


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


SHELLS = ("sh", "bash", "zsh", "dash", "ksh", "mksh", "csh", "tcsh", "fish")


OPERATOR_CHARS = "();<>|&\n`"
OPERATOR = re.compile(r"[<>]\(|;;&|&>>|<<<|\n|;;|;&|&&|\|\||\|&|&>|>>|<<|<&|>&|<>|>\||[();<>|&`]")
WORD_START = " \t\n;&|()<>`"


def shell_tokens(command: str) -> list:
    """The words of a shell command with quotes removed, and its control operators as separate tokens: `a&&b;(c)` gives `a && b ; ( c )`.

    A newline outside quotes separates commands as `;` does, so it is kept as
    an operator. Comments, heredoc bodies and backslash-newlines are dropped
    first, by `shell_source`, and braces are expanded, by `expand_braces`.
    shlex joins adjacent operators into one token,
    `;>` or `&&>`, so each run is split back into the operators it holds. A
    command shlex cannot read, such as `$'it\\'s'`, is split at operators and
    whitespace outside quotes instead, each quoted span kept whole.
    """
    script = expand_braces(shell_source(command))
    lexer = shlex.shlex(script, posix=True, punctuation_chars=OPERATOR_CHARS)
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        tokens = [unquote(token) for token in re.findall(FALLBACK_TOKEN, script)]
    return [part for token in tokens for part in (OPERATOR.findall(token) if is_operator(token) else [token])]


QUOTED = r"'[^']*'|\"(?:\\.|[^\"\\])*\""
FALLBACK_TOKEN = re.compile(rf"[();<>|&`\n]+|(?:{QUOTED}|\\.|[^\s();<>|&`'\"\\])+|['\"\\]")


def unquote(token: str) -> str:
    return re.sub(rf"{QUOTED}|\\.", lambda match: match.group(0)[1:] if match.group(0)[0] == "\\" else match.group(0)[1:-1], token)


ANSI_C = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\", "'": "'", '"': '"', "?": "?"}
ANSI_C_NUMBER = re.compile(r"\\(?:([0-7]{1,3})|x([0-9A-Fa-f]{1,2})|u([0-9A-Fa-f]{1,4})|U([0-9A-Fa-f]{1,8})|c(.))", re.S)


def ansi_c_escape(command: str, index: int) -> tuple:
    """The text the backslash escape at `index` inside `$'...'` stands for, as bash decodes it, and how many characters it takes: `\\x67` is `g`, `\\147` is `g`."""
    letter = command[index + 1 : index + 2]
    if letter in ANSI_C:
        return ANSI_C[letter], 2
    match = ANSI_C_NUMBER.match(command, index)
    if not match:
        return command[index : index + 2], 2
    octal, byte, short, long, control = match.groups()
    if control is not None:
        return chr(ord(control) & 0x1F), match.end() - index
    code = int(octal, 8) & 0xFF if octal else int(byte or short or long, 16)
    return (chr(code) if code <= 0x10FFFF else match.group(0)), match.end() - index


def ansi_c_close(command: str, index: int) -> int:
    """The index of the `'` that closes the `$'...'` span whose text starts at `index`, or the end of `command`.

    A backslash always takes the character after it, as bash and zsh read it,
    so `$'\\c'` closes at its second quote however `\\c` decodes.
    """
    while index < len(command) and command[index] != "'":
        index += 2 if command[index] == "\\" else 1
    return min(index, len(command))


def ansi_c_text(span: str) -> str:
    """The text of a `$'...'` span between its quotes, decoded as bash decodes it, up to a NUL, where bash stops reading the word's text."""
    text = []
    index = 0
    while index < len(span):
        if span[index] == "\\":
            decoded, length = ansi_c_escape(span, index)
            text.append(decoded)
            index += length
        else:
            text.append(span[index])
            index += 1
    return "".join(text).split("\0", 1)[0]


def dollar_run(command: str, index: int) -> int:
    """The index just past the run of `$` that starts at `index`."""
    end = index
    while command.startswith("$", end):
        end += 1
    return end


BRACES = 10_000
BRACE_CHARACTERS = 1_000_000


class Unreadable(Exception):
    """A call the reader will not finish, such as one whose braces expand past BRACES words: a hook blocks it rather than half reading it."""


class ShellsDiffer(Unreadable):
    """A call bash and zsh read differently, such as `$$'\\''`, which bash reads as a plain quote after `$$` and zsh as a `$'...'` quote: a hook blocks it rather than read it one way."""


def read_error(exc: Exception) -> str:
    return str(exc) if isinstance(exc, ShellsDiffer) else type(exc).__name__


def expand_braces(script: str) -> str:
    """`script` with each unquoted brace expression expanded as bash expands it before running a command: `{git,tag} v1` reads `git tag v1` and `app.py{,.bak}` reads `app.py app.py.bak`.

    A quoted or escaped brace, `${...}`, and a brace holding no top-level comma
    and no `..` sequence stay as they are, as in `{ echo; }` or `find -exec
    {} ;`. Expansion multiplies across a word, so past BRACES words or
    BRACE_CHARACTERS characters in all the call is Unreadable.
    """
    if "{" not in script:
        return script
    budget = [BRACES, BRACE_CHARACTERS]
    kept = []
    word = []
    quote = ""
    braces = 0
    index = 0
    while index < len(script):
        char = script[index]
        if char == "\\" and quote != "'":
            word.append(script[index : index + 2])
            index += 2
            continue
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif script.startswith("${", index):
            braces += 1
            word.append("${")
            index += 2
            continue
        elif braces and char == "}":
            braces -= 1
        elif not braces and char in WORD_START:
            kept.extend(expand_word("".join(word), budget))
            kept.append(char)
            word = []
            index += 1
            continue
        word.append(char)
        index += 1
    kept.extend(expand_word("".join(word), budget))
    return "".join(kept)


def expand_word(word: str, budget: list) -> list:
    """`word` with its brace expressions expanded, as text joined by spaces, each result keeping its quotes."""
    if "{" not in word:
        return [word]
    marks = unquoted_positions(word)
    pairs = {}
    stack = []
    for mark in marks:
        char = word[mark]
        if char == "{":
            stack.append((mark, []))
        elif char == "," and stack:
            stack[-1][1].append(mark)
        elif char == "}" and stack:
            open_, commas = stack.pop()
            pairs[open_] = (mark, commas)
    words = expand_range(word, marks, pairs, 0, len(word), budget)
    return [" ".join(part for part in words if part)]


def expand_range(word: str, marks: list, pairs: dict, low: int, high: int, budget: list) -> list:
    """The words `word[low:high]` expands to.

    Each `{` is paired with its `}` once, by `expand_word`, so a word is read in
    one pass however its braces nest. A brace that is neither a list nor a
    sequence stays literal and the braces inside it are still expanded, as bash
    does: `{a{b,c}}` reads `{ab} {ac}`.
    """
    segments = []
    literal = low
    position = bisect.bisect_left(marks, low)
    while position < len(marks) and marks[position] < high:
        open_ = marks[position]
        close, commas = pairs.get(open_, (high, None))
        options = None
        if close < high and commas:
            spend_braces(budget, 1, 0)
            bounds = [open_, *commas, close]
            options = [option for start, end in zip(bounds, bounds[1:]) for option in expand_range(word, marks, pairs, start + 1, end, budget)]
        elif close < high and close - open_ <= 64:
            options = sequence(word[open_ + 1 : close], budget)
        if options is None:
            position += 1
            continue
        segments += [[word[literal:open_]], options]
        literal = close + 1
        position = bisect.bisect_right(marks, close)
    segments.append([word[literal:high]])
    count = 1
    for options in segments:
        count *= len(options)
    spend_braces(budget, count, sum(sum(map(len, options)) * (count // len(options)) for options in segments))
    words = [""]
    for options in segments:
        words = [done + option for done in words for option in options]
    return words


def unquoted_positions(word: str) -> list:
    """The index of each character of `word` outside quotes, escapes and `${...}`."""
    marks = []
    quote = ""
    braces = 0
    index = 0
    while index < len(word):
        char = word[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif word.startswith("${", index):
            braces += 1
            index += 2
            continue
        elif braces:
            braces -= char == "}"
        else:
            marks.append(index)
        index += 1
    return marks


SEQUENCE = re.compile(r"(-?\d+)\.\.(-?\d+)(?:\.\.(-?\d+))?|([A-Za-z])\.\.([A-Za-z])(?:\.\.(-?\d+))?")


def sequence(body: str, budget: list):
    """The words of a `{x..y}` or `{x..y..step}` sequence of integers or single letters, or None when `body` is not one.

    A range between letters of different case covers the characters between
    them, such as `[`, `\\` and a backtick in `{Z..a}`, so every character
    that is not a letter or digit is escaped: the expansion goes back into
    source text that is read again, and must not open or close a quote there.
    """
    match = SEQUENCE.fullmatch(body)
    if not match:
        return None
    first, last, step, first_letter, last_letter, letter_step = match.groups()
    start, end = (int(first), int(last)) if first is not None else (ord(first_letter), ord(last_letter))
    step = abs(int(step or letter_step or 1)) or 1
    spend_braces(budget, abs(end - start) // step + 1, 0)
    values = range(start, end + 1, step) if start <= end else range(start, end - 1, -step)
    if first is None:
        return [re.sub(r"[^A-Za-z0-9]", r"\\\g<0>", chr(value)) for value in values]
    width = max(len(first), len(last)) if any(re.match(r"-?0\d", number) for number in (first, last)) else 0
    return [f"{value:0{width}d}".replace("-", "\\-") for value in values]


def spend_braces(budget: list, words: int, characters: int) -> None:
    budget[0] -= words
    budget[1] -= characters
    if budget[0] < 0 or budget[1] < 0:
        raise Unreadable


def heredoc_at(command: str, index: int):
    """The heredoc whose `<<` is at `index`, as (end of its delimiter, strip_tabs, delimiter, expands), or None.

    The delimiter is the whole word after `<<`, up to whitespace or an
    operator, with its quotes removed, and the body expands only when no quote
    or backslash appears anywhere in it, as in bash: `<<E'OF'` ends at a line
    `EOF` and is literal, `<<E:OF` ends at a line `E:OF`. A `$'...'` span is
    decoded, so `<<$'EOF'` ends at a line `EOF`. bash and zsh end `<<$"EOF"`
    and `<<$$'EOF'` at different lines, so those raise ShellsDiffer.
    """
    if not command.startswith("<<", index) or command.startswith("<<<", index):
        return None
    position = index + 2
    strip_tabs = command.startswith("-", position)
    position += strip_tabs
    while command[position : position + 1] in (" ", "\t"):
        position += 1
    parts = []
    quoted = False
    while position < len(command) and command[position] not in " \t\n;&|()<>":
        char = command[position]
        end = dollar_run(command, position)
        if end > position and command[end : end + 1] not in ("'", '"'):
            parts.append(command[position:end])
            position = end
        elif end > position:
            if end - position > 1 or command[end] == '"':
                raise ShellsDiffer(f"bash and zsh end a heredoc whose delimiter starts {command[position:end + 1]} at different lines")
            quoted = True
            close = ansi_c_close(command, end + 1)
            if close >= len(command):
                return None
            parts.append(ansi_c_text(command[end + 1 : close]))
            position = close + 1
        elif char == "\\":
            quoted = True
            parts.append(command[position + 1 : position + 2])
            position += 2
        elif char in "'\"":
            quoted = True
            end = position + 1
            while end < len(command) and command[end] != char:
                end += 2 if char == '"' and command[end] == "\\" else 1
            if end >= len(command):
                return None
            span = command[position + 1 : end]
            parts.append(re.sub(r'\\([\\"$`])', r"\1", span) if char == '"' else span)
            position = end + 1
        else:
            parts.append(char)
            position += 1
    if not parts:
        return None
    return position, strip_tabs, "".join(parts), not quoted


def shell_source(command: str, bodies=None) -> str:
    """`command` without what the shell does not run as commands: `#` comments, the body of each heredoc, and each backslash-newline, which the shell deletes.

    A `#` starts a comment only at the start of a word, outside quotes and
    `${...}`, so `a\\ #b` and `${x/ #/}` do not. A `<<` inside `((...))`,
    `$((...))` or `$[...]` is a shift, not a heredoc. A heredoc whose closing
    line never comes keeps its body, so a missing delimiter cannot hide the
    lines after it. When `bodies` is a list, the body of each heredoc whose
    delimiter is unquoted is appended to it: the shell still runs `$(...)` and
    backticks there. Each `$'...'` span is written as the plain single-quoted
    text it decodes to. After an even run of `$`, bash reads a plain quote and
    zsh a `$'...'` one, so where a backslash makes them end it apart, the call
    raises ShellsDiffer.
    """
    kept = []
    pending = []
    quote = ""
    arithmetic = 0
    brackets = 0
    braces = 0
    at_word_start = True
    index = 0
    while index < len(command):
        char = command[index]
        starts_word = at_word_start
        at_word_start = False
        if char == "\\" and quote != "'":
            if command[index + 1 : index + 2] != "\n":
                kept.append(command[index : index + 2])
            index += 2
            continue
        if quote:
            if char == quote:
                quote = ""
        elif char == "$" and command[index + 1 : index + 2] in ("$", "'"):
            end = dollar_run(command, index)
            if not command.startswith("'", end):
                kept.append(command[index : end - 1])
                index = end - 1
                continue
            if (end - index) % 2:
                close = ansi_c_close(command, end + 1)
                text = ansi_c_text(command[end + 1 : close]).replace("'", "'\\''")
                kept.append(command[index : end - 1] + "'" + text + ("'" if close < len(command) else ""))
                index = close + 1
                continue
            plain = command.find("'", end + 1)
            if plain != -1 and "\\" in command[end + 1 : plain]:
                raise ShellsDiffer(f"bash and zsh read {command[index:plain + 1]} differently: bash as a plain quote after $$, zsh as a $'...' quote")
            kept.append(command[index:end])
            index = end
            continue
        elif char in "'\"":
            quote = char
        elif char == "#" and starts_word and not braces:
            end = command.find("\n", index)
            index = len(command) if end == -1 else end
            continue
        elif command.startswith("${", index):
            braces += 1
            kept.append("${")
            index += 2
            continue
        elif braces and char == "}":
            braces -= 1
        elif command.startswith("((", index):
            arithmetic += 2
            kept.append("((")
            index += 2
            at_word_start = True
            continue
        elif arithmetic and char in "()":
            arithmetic += 1 if char == "(" else -1
        elif command.startswith("$[", index):
            brackets += 1
            kept.append("$[")
            index += 2
            continue
        elif brackets and char in "[]":
            brackets += 1 if char == "[" else -1
        elif char == "\n" and pending:
            kept.append(char)
            index = skip_heredoc_bodies(command, index + 1, pending, bodies)
            pending = []
            at_word_start = True
            continue
        elif command.startswith("<<<", index):
            kept.append("<<<")
            index += 3
            continue
        elif char == "<" and not arithmetic and not brackets and (heredoc := heredoc_at(command, index)):
            end, strip_tabs, delimiter, expands = heredoc
            pending.append((strip_tabs, delimiter, expands))
            kept.append(command[index:end] if expands else "<<" + "-" * strip_tabs + "'" + delimiter.replace("'", "'\\''") + "'")
            index = end
            continue
        kept.append(char)
        at_word_start = not quote and char in WORD_START
        index += 1
    return "".join(kept)


def skip_heredoc_bodies(command: str, index: int, pending: list, bodies=None) -> int:
    """The index just past the closing line of each heredoc in `pending`, read in order from `index`.

    Stops at the start of the first body whose closing line never comes. The
    body of each heredoc that expands is appended to `bodies` when it is a list.
    """
    for strip_tabs, delimiter, expands in pending:
        starts = line_starts(command)[1 if strip_tabs else 0].get(delimiter, [])
        found = bisect.bisect_left(starts, index)
        if found == len(starts):
            return index
        position = starts[found]
        if expands and bodies is not None:
            bodies.append(command[index:position])
        end = command.find("\n", position)
        index = len(command) if end == -1 else end + 1
    return index


@functools.lru_cache(maxsize=8)
def line_starts(command: str) -> tuple:
    """Where each line of `command` starts, by its text, and by its text with leading tabs stripped.

    Built once per command, so finding a heredoc's closing line costs a lookup
    rather than a scan to the end of the call for every heredoc that never closes.
    """
    plain = {}
    stripped = {}
    position = 0
    for line in command.split("\n"):
        plain.setdefault(line, []).append(position)
        stripped.setdefault(line.lstrip("\t"), []).append(position)
        position += len(line) + 1
    return plain, stripped


def is_operator(token: str) -> bool:
    return bool(token) and all(char in OPERATOR_CHARS for char in token)


def find_commit(tokens: list):
    """The `-C` directories of the first `git commit` in `tokens`, or None when there is none.

    `git` is matched by basename, so `/usr/bin/git` counts, and the script of
    `bash -c` or `eval` is searched too, so rewording a commit cannot hide it.
    """
    for index, token in enumerate(tokens):
        name = os.path.basename(token)
        rest = tokens[index + 1 :]
        if name in SHELLS:
            script = shell_script(rest)
            if script is not None:
                found = find_commit(shell_tokens(script))
                if found is not None:
                    return found
            continue
        if name == "eval":
            script = []
            for word in rest:
                if is_operator(word):
                    break
                script.append(word)
            found = find_commit(shell_tokens(" ".join(script)))
            if found is not None:
                return found
            continue
        if name != "git":
            continue
        dirs, rest = git_options(rest)
        if rest and rest[0] == "commit":
            return dirs
    return None


def shell_script(words: list):
    """The script a shell runs with `-c`, from the words after the shell's name, or None.

    The first short option cluster holding `c` marks it, so options before it,
    long ones and option arguments included, cannot hide it: `bash --norc -c`,
    `bash -o pipefail -c`, `sh -lc`. The shell reads options after it too, so
    the script is the first word after those and after a `--`: `bash -c -e`,
    `bash -c -- 'script'`.
    """
    for index, word in enumerate(words):
        if is_operator(word):
            return None
        if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", word):
            rest = words[index + 1 :]
            while rest and rest[0][:1] in ("-", "+") and not is_operator(rest[0]):
                option = rest.pop(0)
                if option == "--":
                    break
                if option in ("-o", "+o", "-O", "+O") and rest:
                    rest.pop(0)
            return rest[0] if rest and not is_operator(rest[0]) else None
    return None


def git_options(words: list):
    """Skips git's global options in the words after `git`. Returns the `-C` directories and the words from the subcommand on."""
    dirs = []
    rest = list(words)
    while rest and rest[0].startswith("-"):
        flag = rest.pop(0)
        if flag in ("-C", "-c", "--git-dir", "--work-tree") and rest:
            value = rest.pop(0)
            if flag == "-C":
                dirs.append(value)
    return dirs, rest


def is_git_commit(command: str) -> bool:
    """True for `git commit` anywhere in the command, allowing global options such as `git -C dir commit`."""
    return find_commit(shell_tokens(command)) is not None


def commit_checkout(event: dict, command: str) -> Path:
    """The top level of the checkout a `git commit` in `command` lands in.

    Starts from the event's `cwd`, the shell's real directory, falling back to
    the project directory; then applies a leading `cd <dir> &&` or `cd <dir>;`
    and any `git -C <dir>` on the commit, as the shell would. A directory that
    is not a checkout, such as an unexpanded `cd "$PWD"`, falls back to the
    shell's directory. Inside a worktree this differs from `CLAUDE_PROJECT_DIR`,
    which always names the main checkout.
    """
    shell = Path(event.get("cwd") or project_dir())
    tokens = shell_tokens(command)
    directory = shell
    if len(tokens) >= 3 and tokens[0] == "cd" and tokens[2] in ("&&", ";"):
        directory = directory / os.path.expanduser(tokens[1])
    for value in find_commit(tokens) or []:
        directory = directory / os.path.expanduser(value)
    for candidate in (directory, shell, project_dir()):
        top = git(candidate, "rev-parse", "--show-toplevel")
        if top:
            return Path(top.strip())
    return directory


def same_repository(first: Path, second: Path) -> bool:
    """True when both paths are checkouts of one repository: the same checkout, or a worktree and its main checkout."""
    common = [git(path, "rev-parse", "--git-common-dir") for path in (first, second)]
    if None in common:
        return False
    return (first / common[0].strip()).resolve() == (second / common[1].strip()).resolve()


def commits_all_tracked(command: str) -> bool:
    tokens = command.split()
    return any(token in ("-a", "--all") or (token.startswith("-") and not token.startswith("--") and "a" in token[1:]) for token in tokens)
