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
    an operator. Comments, heredoc bodies, backslash-newlines and the scripts
    of substitutions inside double quotes are dropped first, by
    `shell_source`, and braces are expanded, by `expand_braces`.
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
    return [part for token in tokens for part in (OPERATOR.findall(token) if is_operator(token) else brace_group_words(token))]


def brace_group_words(word: str) -> list:
    """`word` with the braces of a zsh brace group as words of their own.

    zsh opens a brace group at a `{` that starts a command word and closes it
    at a `}` that ends a word, so `{git tag v1}` runs `git tag v1`. The `{` is
    split off wherever it starts a word, and a `}` wherever it ends one it
    does not close, so a program name behind one is read; `{}` stays whole,
    as zsh keeps it. Quotes are already gone, so a quoted brace is split too,
    except in a word holding whitespace, which only quotes make: that word is
    a script or an argument, such as the one `zsh -c '{git tag v1}'` reads.
    """
    if any(char.isspace() for char in word):
        return [word]
    words = []
    while word.startswith("{") and word != "{}" and len(word) > 1:
        words.append("{")
        word = word[1:]
    if len(word) > 1 and word.endswith("}") and word.count("}") > word.count("{"):
        return [*words, word[:-1], "}"]
    return [*words, word]


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


def escaped_close(command: str, index: int, mark: str) -> int:
    """The index of the first `mark` at or after `index` that no backslash escapes, or the end of `command`.

    This closes a `$'...'` span or a backtick span. A backslash always takes
    the character after it, as bash and zsh read it, so `$'\\c'` closes at its
    second quote however `\\c` decodes.
    """
    while index < len(command) and command[index] != mark:
        index += 2 if command[index] == "\\" else 1
    return min(index, len(command))


BACKTICK_ESCAPE = re.compile(r"\\([\\`$\n])")
QUOTED_BACKTICK_ESCAPE = re.compile(r'\\([\\`$"\n])')


def backtick_script(span: str, quoted: bool = False) -> str:
    """The script of a backtick span, as bash and zsh make it before reading it.

    One pass from the left takes the backslash off `\\\\`, `\\``, `\\$` and,
    inside double quotes, `\\"`, and deletes each backslash-newline; any other
    backslash stays. So `\\\\` before a newline leaves `\\` and the newline,
    which the script then reads by its own quotes.
    """
    escape = QUOTED_BACKTICK_ESCAPE if quoted else BACKTICK_ESCAPE
    return escape.sub(lambda match: "" if match.group(1) == "\n" else match.group(1), span)


def ansi_c_span(command: str, index: int):
    """The index of the `'` closing the `$'...'` span that the run of `$` at `index` opens, or None when it opens none.

    After an even run of `$`, bash reads a plain quote and zsh a `$'...'` one,
    so where a backslash makes them end it apart, the call raises ShellsDiffer.
    """
    end = dollar_run(command, index)
    if not command.startswith("'", end):
        return None
    if (end - index) % 2:
        return escaped_close(command, end + 1, "'")
    plain = command.find("'", end + 1)
    if plain != -1 and "\\" in command[end + 1 : plain]:
        raise ShellsDiffer(f"bash and zsh read {command[index:plain + 1]} differently: bash as a plain quote after $$, zsh as a $'...' quote")
    return None


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


class Unclosed(Unreadable):
    """A call holding a substitution or `${...}` in double quotes that never closes: the shells reject it, and reading on would hide the rest of the call."""


class Unmodelled(Unreadable):
    """A call holding a form the reader does not model, where reading it one way could hide the text after it: a `case` inside a substitution, a `#` comment ending in a backslash inside one, or a backslash-newline that changes where a quote, substitution, heredoc or comment ends."""


def read_error(exc: Exception) -> str:
    return str(exc) if isinstance(exc, (ShellsDiffer, Unclosed, Unmodelled)) else type(exc).__name__


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
            close = escaped_close(command, end + 1, "'")
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


def shell_source(command: str, bodies=None, spans=None) -> str:
    """`command` as `source_text` reads it, with each backslash-newline read as bash and zsh read it.

    They delete one before reading anything else, except in literal text:
    inside single quotes or `$'...'`, where it stays for a `bash -c` or `eval`
    script to read in turn, in a heredoc body whose delimiter is quoted, and
    at the end of a `#` comment, which still ends at its line. A token split
    by one is only whole once it is deleted, so a call holding one is read
    twice: as written, which finds the literal ones in comments and heredoc
    bodies, and with every other one deleted. When the two readings differ
    once their own backslash-newlines are deleted, one of them sits where it
    changes where a quote, substitution, heredoc or comment ends, and the call
    raises Unmodelled. Otherwise the written reading is returned, which keeps
    the ones in quotes, with each heredoc body that expands joined, as the
    shells join it.
    """
    if "\\\n" not in command:
        return source_text(command, bodies, spans)
    literal = []
    written_bodies, written_spans = [], []
    written = source_text(command, written_bodies, written_spans, literal)
    joined_bodies, joined_spans = [], []
    text = source_text(joined(command, set(literal)), joined_bodies, joined_spans)
    if flattened(written, written_bodies, written_spans) != flattened(text, joined_bodies, joined_spans):
        raise Unmodelled("a backslash-newline that changes where a quote, substitution, heredoc or comment ends")
    if bodies is not None:
        bodies.extend(joined_bodies)
    if spans is not None:
        spans.extend(written_spans)
    return written


CONTINUATION = re.compile(r"\\(?:\n|.)", re.S)
COMMENT_IN_SUBSTITUTION = "a `#` comment ending in a backslash inside a substitution, which bash and zsh end at different places"
LITERAL_BODY_IN_SUBSTITUTION = "bash and zsh end a quoted heredoc body holding a backslash-newline inside a substitution at different places: bash joins its lines, zsh keeps them"


def flattened(text: str, bodies: list, spans: list) -> tuple:
    return joined(text), [joined(body) for body in bodies], [joined(span) for span in spans]


def joined(text: str, kept=()) -> str:
    """`text` with each backslash-newline deleted, except one whose backslash is at an index in `kept`, a backslash escaped by another kept."""
    return CONTINUATION.sub(lambda match: "" if match.group(0) == "\\\n" and match.start() not in kept else match.group(0), text)


def continuations(command: str, start: int, end: int) -> list:
    """The index of the backslash of each backslash-newline between `start` and `end`, a backslash escaped by another not counted."""
    return [match.start() for match in CONTINUATION.finditer(command, start, end) if match.group(0) == "\\\n"]


def comment_continues(command: str, index: int, end: int) -> bool:
    """True when the `#` comment from `index` to the newline at `end` ends in a backslash no other escapes: bash and zsh still end it at that newline, except inside a substitution, where they part."""
    comment = command[index:end]
    return (len(comment) - len(comment.rstrip("\\"))) % 2 == 1


def substitution_holds(command: str, opens: list, settled: list, index: int) -> bool:
    """True when a `$(`, `<(` or `>(` span whose `(` is at an index in `opens`, in order, is still open at `index`.

    `settled[0]` counts the spans already known to close before an earlier
    index, and advances past each span that closes before this one together
    with the spans nested in it, so a call holding many of them and many
    comments measures each top-level span once.
    """
    while settled[0] < len(opens):
        close = closing_paren(command, opens[settled[0]])
        if close > index:
            return True
        settled[0] = bisect.bisect_right(opens, close, settled[0] + 1)
    return False


WORD, ARITHMETIC, ARRAY, GLOB = "word", "arithmetic", "array", "glob"
HASH_AFTER_ARRAY = "bash and zsh read a `#` straight after an array's `)` differently: bash as part of the word, zsh as a comment"
HASH_IN_GLOB = "bash and zsh read a `#` inside or straight after a `(...)` that opens in the middle of a word, such as `x(N)#y`, differently: zsh as part of the word's glob group, bash as a syntax error"


def source_text(command: str, bodies=None, spans=None, literal=None) -> str:
    """`command` without what the shell does not run as commands: `#` comments, the body of each heredoc, and each backslash-newline, which the shell deletes.

    A `#` starts a comment only at the start of a word, outside quotes,
    `${...}` and arithmetic, so `a\\ #b`, `${x/ #/}` and `(( ##a ))` do not,
    and the `)` of `$(...)`, `<(...)`, `>(...)` or `$((...))` does not end a
    word, so `$(a)#b` does not either. A `#` straight after an array's `)`,
    part of the word to bash and a comment to zsh, raises ShellsDiffer, and so
    does one inside or straight after a `(...)` that opens in the middle of a
    word, a glob group to zsh and a syntax error to bash. A `((` is arithmetic
    where `arithmetic_end` reads it so, a quote inside it or `$[...]` raises
    ShellsDiffer, and a `<<` there is a shift, not a heredoc. Since a `case`
    pattern's `)` would close a parenthesis it does not open, a `case` inside
    a `$(...)`, `<(...)` or `>(...)` span raises Unmodelled. A heredoc whose closing
    line never comes keeps its body, so a missing delimiter cannot hide the
    lines after it. When `bodies` is a list, the body of each heredoc whose
    delimiter is unquoted is appended to it: the shell still runs `$(...)` and
    backticks there. Each `$'...'` span is written as the plain single-quoted
    text it decodes to. Double-quoted text is read by `double_quoted`, so a
    quote inside a substitution there cannot end it, and each substitution's
    script is appended to `spans` when it is a list. A backtick span ends at
    its first unescaped backtick, as both shells end it before reading what
    is inside; its script, from `backtick_script`, is appended to `spans` and
    its own reading kept in place of its text, and a reading that leaves a
    quote open raises Unclosed, since that quote would pair with a later one.

    A backslash-newline inside single quotes or `$'...'` is kept, as the
    shells keep it; in a backtick span `backtick_script` has already deleted
    it. One that ends a `#` comment, or sits in a heredoc body whose delimiter is
    quoted, is kept as well, and the index of its backslash is appended to
    `literal` when it is a list; inside a substitution, where bash and zsh
    part, the comment raises Unmodelled and the body ShellsDiffer.
    """
    kept = []
    pending = []
    opens = []
    settled = [0]
    quote = ""
    parens = []
    words = 0
    matches = {}
    brackets = 0
    braces = 0
    at_word_start = True
    index = 0
    while index < len(command):
        char = command[index]
        starts_word = at_word_start
        at_word_start = False
        arithmetic = bool(parens) and parens[-1] == ARITHMETIC
        if char == "\\" and not quote:
            if command[index + 1 : index + 2] != "\n":
                kept.append(command[index : index + 2])
            else:
                at_word_start = starts_word
            index += 2
            continue
        if not quote and command.startswith(("$(", "<(", ">("), index):
            opens.append(index + 1)
        if quote:
            if char == quote:
                quote = ""
        elif (arithmetic or brackets) and (char in "'\"" or char == "$" and command.startswith("'", dollar_run(command, index))):
            raise ShellsDiffer(QUOTE_IN_ARITHMETIC)
        elif char == "$" and command[index + 1 : index + 2] in ("$", "'"):
            end = dollar_run(command, index)
            close = ansi_c_span(command, index)
            if close is not None:
                span = command[end + 1 : close]
                text = ansi_c_text(span).replace("'", "'\\''")
                kept.append(command[index : end - 1] + "'" + text + ("'" if close < len(command) else ""))
                index = close + 1
                continue
            if not command.startswith("'", end):
                end -= 1
            kept.append(command[index:end])
            index = end
            continue
        elif char == '"':
            end, text = double_quoted(command, index + 1, spans)
            kept.append('"' + text + ('"' if end < len(command) else ""))
            index = end + 1
            continue
        elif char == "'":
            quote = char
        elif char == "#" and starts_word and not braces and parens and parens[-1] == GLOB:
            raise ShellsDiffer(HASH_IN_GLOB)
        elif char == "#" and starts_word and not braces and not arithmetic and not brackets:
            end = command.find("\n", index)
            if end != -1 and comment_continues(command, index, end):
                if substitution_holds(command, opens, settled, index):
                    raise Unmodelled(COMMENT_IN_SUBSTITUTION)
                if literal is not None:
                    literal.append(end - 1)
            index = len(command) if end == -1 else end
            continue
        elif command.startswith("${", index):
            braces += 1
            kept.append("${")
            index += 2
            continue
        elif braces and char == "}":
            braces -= 1
        elif char == "(" and not braces:
            before = command[index - 1 : index]
            if command.startswith("((", index) and (before == "$" or starts_word and not arithmetic) and arithmetic_end(command, index + 1, matches=matches) is not None:
                parens.extend([WORD if before == "$" else "", ARITHMETIC])
                words += before == "$"
                kept.append("((")
                index += 2
                at_word_start = True
                continue
            if before == "$" or before in ("<", ">") and not arithmetic:
                parens.append(WORD)
            elif arithmetic:
                parens.append(ARITHMETIC)
            elif parens and parens[-1] == GLOB or not starts_word and before != "=" and not command.startswith(")", index + 1):
                parens.append(GLOB)
            else:
                parens.append(ARRAY if before == "=" else "")
            words += parens[-1] == WORD
        elif char == ")" and parens and not braces:
            kind = parens.pop()
            words -= kind == WORD
            if kind in (ARRAY, GLOB) and command.startswith("#", index + 1):
                raise ShellsDiffer(HASH_AFTER_ARRAY if kind == ARRAY else HASH_IN_GLOB)
            kept.append(char)
            at_word_start = kind in ("", ARITHMETIC)
            index += 1
            continue
        elif words and not braces and char == "c" and keyword_position(command, index, 0) and word_at(command, index, "case"):
            raise Unmodelled(CASE_IN_SUBSTITUTION)
        elif command.startswith("$[", index):
            arithmetic_end(command, index + 1, "[]")
            brackets += 1
            kept.append("$[")
            index += 2
            continue
        elif brackets and char in "[]":
            brackets += 1 if char == "[" else -1
        elif char == "\n" and pending:
            kept.append(char)
            found = []
            index = skip_heredoc_bodies(command, index + 1, pending, bodies, found)
            if found and substitution_holds(command, opens, settled, index):
                raise ShellsDiffer(LITERAL_BODY_IN_SUBSTITUTION)
            if literal is not None:
                literal.extend(found)
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
        elif char == "`":
            end = escaped_close(command, index + 1, "`")
            script = backtick_script(command[index + 1 : end])
            if spans is not None:
                spans.append(script)
            reading = shell_source(script)
            if quote_left_open(reading):
                raise Unclosed(QUOTE_IN_BACKTICKS)
            kept.append("`" + reading + command[end : end + 1])
            index = end + 1
            continue
        kept.append(char)
        at_word_start = not quote and char in WORD_START
        index += 1
    return "".join(kept)


QUOTE_IN_BACKTICKS = "a backtick span whose script leaves a quote open"


def quote_left_open(reading: str) -> bool:
    """True when the reading `shell_source` gives ends inside a quote: kept in place of a backtick span, its open quote would pair with a later one in the call and hide the text between."""
    index = 0
    while index < len(reading):
        char = reading[index]
        if char == "\\":
            index += 2
            continue
        if char in "'\"":
            end = reading.find("'", index + 1) if char == "'" else escaped_close(reading, index + 1, '"')
            if end == -1 or end >= len(reading):
                return True
            index = end
        index += 1
    return False


def double_quoted(command: str, index: int, spans=None) -> tuple:
    """The double-quoted text whose first character is at `index`, just past its opening quote, as (index of its closing quote or the end of `command`, its text).

    Inside it, `$(...)`, a backtick span and `${...}` each open a context of
    their own, as in bash and zsh, so in `"$(echo "it's")"` the quote closes
    at the last `"`. The text keeps each of them as an empty `$()` or `${}`,
    which no later reader can mistake for a quote, and drops each
    backslash-newline. A run of `$` is read whole, as in `dollar_quoted`.
    When `spans` is a list, the script of each substitution is appended to it.
    A substitution or `${...}` that never closes raises Unclosed.
    """
    text = []
    while index < len(command):
        char = command[index]
        if char == '"':
            return index, "".join(text)
        if char == "\\":
            if command[index + 1 : index + 2] != "\n":
                text.append(command[index : index + 2])
            index += 2
            continue
        if command.startswith("$$", index):
            end = dollar_quoted(command, index, in_parameter=False)
            text.append(command[index:end])
            index = end
            continue
        if (end := substitution_end(command, index, spans)) is not None:
            text.append("$()")
        elif command.startswith("${", index):
            end = parameter_close(command, index + 2, spans)
            if end >= len(command):
                raise Unclosed('a "${...}" inside double quotes never closes')
            text.append("${}")
        else:
            text.append(char)
            end = index
        index = end + 1
    return len(command), "".join(text)


def dollar_quoted(command: str, index: int, in_parameter: bool) -> int:
    """For the run of two or more `$` at `index` inside double quotes, the index of its last `$` when that one can open a span, or just past the run when it cannot.

    bash and zsh expand `$$` as the PID, so after an even run a `(` or `{` is
    literal text, and after an odd run the last `$` opens `$(...)` or
    `${...}`. `literal_bracket_close` checks the bracket after an even run.
    """
    end = dollar_run(command, index)
    if (end - index) % 2:
        return end - 1
    literal_bracket_close(command, end, in_parameter)
    return end


LITERAL_BRACKETS = 16
literal_brackets_open = [0]


@functools.lru_cache(maxsize=None)
def literal_bracket_close(command: str, index: int, in_parameter: bool):
    """For the `(` or `{` at `index` after an even run of `$` inside double quotes, the index of the bracket that closes it, or None when no bracket is there.

    bash's parser takes that bracket as opening a span when it looks for the
    closing quote, while zsh reads it as text, so where the two readings would
    end the quote, or the `${...}` it is in when `in_parameter`, at different
    places, the call raises ShellsDiffer. Each answer is cached, so a reading
    that meets the bracket again takes it from here: without that, nesting
    such brackets doubles the reading at every level. Each check scans the
    bracket's whole span, so past LITERAL_BRACKETS nested inside one another,
    which no real command writes, the call is Unreadable.
    """
    bracket = command[index : index + 1]
    if bracket not in ("(", "{"):
        return None
    if literal_brackets_open[0] >= LITERAL_BRACKETS:
        raise Unreadable
    literal_brackets_open[0] += 1
    try:
        close = closing_paren(command, index) if bracket == "(" else parameter_close(command, index + 1)
        agree = close < len(command) and read_as_text_reaches(command, index, close, in_parameter)
    finally:
        literal_brackets_open[0] -= 1
    if not agree:
        raise ShellsDiffer(f"bash and zsh end the double-quoted text holding $${bracket} at different places: bash reads {bracket} as opening a span, zsh as text after the PID")
    return close


def read_as_text_reaches(command: str, index: int, limit: int, in_parameter: bool) -> bool:
    """True when double-quoted text, or the text of a `${...}` inside it when `in_parameter`, read from `index` as zsh reads it, reaches `limit` without closing, and the character at `limit` does not close it either."""
    stop = "}" if in_parameter else '"'
    while index < limit:
        char = command[index]
        if char == "\\":
            index += 2
            continue
        if char == stop:
            return False
        if command.startswith("$$", index):
            end = dollar_run(command, index)
            if (end - index) % 2:
                index = end - 1
            else:
                close = literal_bracket_close(command, end, in_parameter)
                index = end if close is None else close + 1
            continue
        if in_parameter and char == '"':
            index = double_quoted(command, index + 1)[0] + 1
        elif (end := substitution_end(command, index)) is not None:
            index = end + 1
        elif command.startswith("${", index):
            index = parameter_close(command, index + 2) + 1
        else:
            index += 1
    return index == limit and command[limit] != stop


SHELLS_DIFFER_IN_PARAMETER = re.compile(r'[}"`]|\$[({[]')


def parameter_close(command: str, index: int, spans=None) -> int:
    """The index of the `}` that closes the `${...}` inside double quotes whose text starts at `index`, or the end of `command`.

    A `"` opens nested double-quoted text, and `$(...)`, backticks, `${...}`
    and runs of `$` are read as in `double_quoted`, their scripts appended to
    `spans`. bash reads a `'...'` span here as a quote and zsh as literal
    text, so a span holding a character where that changes the reading, such
    as `}` or `"`, raises ShellsDiffer; any other is read as zsh does, and an
    unclosed `'`, which bash rejects, as well.
    """
    while index < len(command):
        char = command[index]
        if char == "}":
            return index
        if char == "\\":
            index += 2
            continue
        if command.startswith("$$", index):
            index = dollar_quoted(command, index, in_parameter=True)
            continue
        if char == '"':
            index = double_quoted(command, index + 1, spans)[0]
        elif char == "'":
            end = command.find("'", index + 1)
            if end != -1 and SHELLS_DIFFER_IN_PARAMETER.search(command, index + 1, end):
                raise ShellsDiffer(f'bash and zsh read {command[index:end + 1]} inside "${{...}}" differently: bash as a quote, zsh as literal text')
        elif (end := substitution_end(command, index, spans)) is not None:
            index = end
        elif command.startswith("${", index):
            index = parameter_close(command, index + 2, spans)
        index += 1
    return len(command)


def substitution_end(command: str, index: int, spans=None):
    """The index of the close of the `$(...)` or backtick span at `index` inside double quotes, or None when neither starts there.

    When `spans` is a list, the span's script is appended to it, a backtick
    span's with `\\\\`, `\\``, `\\$` and `\\"` unescaped, as bash does there. A
    span that never closes raises Unclosed.
    """
    if command.startswith("$(", index):
        end = closing_paren(command, index + 1)
        script = command[index + 2 : end]
    elif command.startswith("`", index):
        end = escaped_close(command, index + 1, "`")
        script = backtick_script(command[index + 1 : end], quoted=True)
    else:
        return None
    if end >= len(command):
        raise Unclosed("a substitution inside double quotes never closes")
    if spans is not None:
        spans.append(script)
    return end


METACHARACTERS = " \t\n;&|()<>"
CASE_IN_SUBSTITUTION = "a `case` inside a substitution"


@functools.lru_cache(maxsize=None)
def closing_paren(command: str, start: int) -> int:
    """The index of the `)` that closes the `(` at `start`, or the end of `command`.

    Parentheses in quoted text, in a backtick span, after a backslash, in a
    `#` comment, in a heredoc body, in a `${...}` or in arithmetic do not
    count. A `case` pattern's `)` would not count either, and a reading that
    took one the wrong way would hide the text after it, so a whole word
    `case` anywhere in the span raises Unmodelled, after a `{` too, where zsh
    opens a brace group, as does a `#` comment
    ending in a backslash, which zsh ends at its line and bash does not;
    `cat case.txt` holds no such word. A heredoc body whose delimiter is
    quoted and that holds a backslash-newline raises ShellsDiffer, since bash
    joins its lines here and zsh does not. A `${...}` holding parentheses that
    do not balance raises ShellsDiffer, since bash 3.2 counts them and zsh
    does not, after a run of `$` of any length too: zsh's lexer takes a `$`
    before `{` as opening one. Double-quoted text is read by `double_quoted`,
    so a substitution nested in it keeps its own quotes. A `((` whose inner
    `(` closes just before the outer `)` is arithmetic, as bash reads `$((`
    and `((`, and so is `$[...]`, as `arithmetic_end` reads them, raising
    ShellsDiffer where bash and zsh part: a `<<` there is a shift, and `<<<`
    is a here-string, never a heredoc. A `((` that is not arithmetic is read twice,
    so each answer is cached: without that, nesting such a span in double
    quotes doubles the reading at every level.
    """
    if command.startswith("((", start):
        end = arithmetic_end(command, start + 1)
        if end is not None:
            return end + 1
    depth = 0
    pending = []
    index = start
    while index < len(command):
        char = command[index]
        if keyword_position(command, index, start) and word_at(command, index, "case"):
            raise Unmodelled(CASE_IN_SUBSTITUTION)
        if char == "\\":
            index += 2
            continue
        if char == "'":
            end = command.find("'", index + 1)
            index = len(command) if end == -1 else end
        elif char == '"':
            index = double_quoted(command, index + 1)[0]
        elif char == "`":
            index = escaped_close(command, index + 1, "`")
        elif char == "$" and command[index + 1 : index + 2] in ("$", "'"):
            close = ansi_c_span(command, index)
            if close is not None:
                index = close + 1
                continue
            end = dollar_run(command, index)
            index = end - 1 if command.startswith("{", end) else end
            continue
        elif command.startswith("$[", index):
            index = arithmetic_end(command, index + 1, "[]")
        elif command.startswith("${", index):
            end = parameter_close(command, index + 2)
            if not parentheses_balance(command, index + 2, end):
                raise ShellsDiffer("bash and zsh end a substitution holding a `${...}` with an unbalanced parenthesis at different places: bash 3.2 counts it, zsh reads the `${...}` whole")
            index = end
        elif char == "#" and index > start and command[index - 1] in WORD_START:
            end = command.find("\n", index)
            if end != -1 and comment_continues(command, index, end):
                raise Unmodelled(COMMENT_IN_SUBSTITUTION)
            index = len(command) if end == -1 else end
            continue
        elif char == "\n" and pending:
            found = []
            index = skip_heredoc_bodies(command, index + 1, pending, literal=found)
            if found:
                raise ShellsDiffer(LITERAL_BODY_IN_SUBSTITUTION)
            pending = []
            continue
        elif command.startswith("<<<", index):
            index += 3
            continue
        elif char == "<" and (heredoc := heredoc_at(command, index)):
            pending.append(heredoc[1:])
            index = heredoc[0]
            continue
        elif char == "(":
            arithmetic = arithmetic_end(command, index + 1) if command.startswith("((", index) else None
            if arithmetic is not None:
                index = arithmetic + 1
            else:
                depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(command)


def keyword_position(command: str, index: int, start: int) -> bool:
    """True when a word at `index`, after `start`, sits where bash or zsh can read it as a keyword: after a metacharacter, or after a run of `{` that does, where zsh opens a brace group."""
    before = index
    while before > start and command[before - 1] == "{":
        before -= 1
    return before > start and command[before - 1] in METACHARACTERS


QUOTE_IN_ARITHMETIC = "bash and zsh read a quote inside arithmetic differently: bash as a quote, zsh as a character"
PARAMETER_IN_ARITHMETIC = "bash and zsh end arithmetic holding a `${...}` with a parenthesis or bracket at different places: bash 3.2 counts it, zsh reads the `${...}` whole"


def arithmetic_end(command: str, start: int, pair: str = "()", matches=None):
    """The index of the bracket that closes the arithmetic `(`, or `[` with `pair` `[]`, at `start`, or None when the `((` holding that `(` is not arithmetic.

    A `((` is arithmetic when its inner `(` closes just before a `)`, as
    bash reads `((` and `$((`, and `$[` always is. bash and zsh read two
    things there apart: a quote, which is a quote to bash and a character to
    zsh, and a bracket inside `${...}`, which bash 3.2 counts and zsh does
    not. So a quote in arithmetic either shell reads raises ShellsDiffer, and
    so does a `${...}` that makes the two readings end it at different places.
    `matches` keeps each reading's scans, so a run of `((` is read once.
    """
    matches = {} if matches is None else matches
    bash, quoted, parameter = bracket_close(command, start, pair, False, matches)
    zsh, zsh_quoted = (bash, False) if not (quoted or parameter) else bracket_close(command, start, pair, True, matches)[:2]
    in_bash = pair == "[]" or command.startswith(")", bash + 1)
    in_zsh = pair == "[]" or command.startswith(")", zsh + 1)
    if (quoted or zsh_quoted) and (in_bash or in_zsh):
        raise ShellsDiffer(QUOTE_IN_ARITHMETIC)
    if in_bash != in_zsh or in_bash and bash != zsh:
        raise ShellsDiffer(PARAMETER_IN_ARITHMETIC)
    return bash if in_bash else None


def bracket_close(command: str, start: int, pair: str, zsh: bool, matches: dict) -> tuple:
    """(the index of the bracket that closes the one at `start`, or the end of `command`; whether a quote comes before it; whether a `${` does), as bash reads arithmetic or, with `zsh`, as zsh does.

    Brackets count unless escaped or in a substitution. bash takes a quote as
    a quote and counts brackets inside `${...}`; zsh takes a quote as a
    character and reads `${...}` whole. One scan records the close of every
    bracket it meets, and where each quote and `${` is, in `matches`.
    """
    closes, quotes, parameters = matches.setdefault((pair, zsh), ({}, [], []))
    if start not in closes:
        opens = []
        braces = 0
        index = start
        while index < len(command):
            char = command[index]
            if char == "\\":
                index += 2
                continue
            if char in "'\"" or command.startswith("$'", index):
                bisect.insort(quotes, index)
                if zsh:
                    pass
                elif char == "$":
                    close = ansi_c_span(command, index)
                    index = len(command) if close is None else close
                elif char == "'":
                    end = command.find("'", index + 1)
                    index = len(command) if end == -1 else end
                else:
                    index = double_quoted(command, index + 1)[0]
            elif char == "`":
                index = escaped_close(command, index + 1, "`")
            elif command.startswith("$(", index):
                index = closing_paren(command, index + 1)
            elif command.startswith("${", index):
                bisect.insort(parameters, index)
                if zsh:
                    braces += 1
                    index += 2
                    continue
            elif braces:
                braces -= char == "}"
            elif char == pair[0]:
                opens.append(index)
            elif char == pair[1] and opens:
                closes[opens.pop()] = index
                if not opens:
                    break
            index += 1
        for unclosed in opens:
            closes[unclosed] = len(command)
    close = closes[start]
    return close, holds(quotes, start, close), holds(parameters, start, close)


def holds(positions: list, start: int, end: int) -> bool:
    """True when the sorted `positions` hold one between `start` and `end`."""
    found = bisect.bisect_right(positions, start)
    return found < len(positions) and positions[found] < end


def parentheses_balance(command: str, index: int, end: int) -> bool:
    """True when the parentheses between `index` and `end` balance, counting as bash 3.2 does inside a substitution: not after a backslash or in quotes."""
    depth = 0
    while index < end:
        char = command[index]
        if char == "\\":
            index += 1
        elif char == "'":
            close = command.find(char, index + 1, end)
            index = end if close == -1 else close
        elif char == '"':
            index = min(double_quoted(command, index + 1)[0], end)
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
        index += 1
    return depth == 0


def word_at(command: str, index: int, word: str) -> bool:
    """True when the word at `index` is exactly `word`: a reserved word ends at a metacharacter, so `case.txt` and `case-x` are not `case`."""
    return command.startswith(word, index) and command[index + len(word) : index + len(word) + 1] in METACHARACTERS


def skip_heredoc_bodies(command: str, index: int, pending: list, bodies=None, literal=None) -> int:
    """The index just past the closing line of each heredoc in `pending`, read in order from `index`.

    Stops at the start of the first body whose closing line never comes. The
    body of each heredoc that expands is appended to `bodies` when it is a
    list, and the backslash of each backslash-newline in a body that does not
    expand is appended to `literal` when it is a list.
    """
    for strip_tabs, delimiter, expands in pending:
        starts = line_starts(command)[1 if strip_tabs else 0].get(delimiter, [])
        found = bisect.bisect_left(starts, index)
        if found == len(starts):
            return index
        position = starts[found]
        if expands and bodies is not None:
            bodies.append(command[index:position])
        if not expands and literal is not None:
            literal.extend(continuations(command, index, position))
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

    `git` is matched by `program_name`, so `/usr/bin/git` and zsh's `=git`
    count, and the script of `bash -c` or `eval` is searched too, so rewording
    a commit cannot hide it.
    """
    for index, token in enumerate(tokens):
        name = program_name(token)
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


def program_name(word: str) -> str:
    """The program `word` names, by basename, read past one leading `=`: zsh expands `=git` to the path of `git`, and bash has no program named `=git`."""
    return os.path.basename(word[1:] if word.startswith("=") else word)


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
