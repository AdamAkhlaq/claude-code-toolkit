"""Shared helpers for the toolkit hooks. Standard library only.

Every hook follows the same contract: read the tool event from stdin, load
`.claude/toolkit.json` from the project, and exit 0 without output when the
config is absent. A hook only ever acts on a project that opted in.
"""

import fnmatch
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


SHELLS = ("sh", "bash", "zsh", "dash")


OPERATOR_CHARS = "();<>|&\n`"
OPERATOR = re.compile(r"[<>]\(|;;&|&>>|<<<|\n|;;|;&|&&|\|\||\|&|&>|>>|<<|<&|>&|<>|>\||[();<>|&`]")
WORD_START = " \t\n;&|()<>`"


def shell_tokens(command: str) -> list:
    """The words of a shell command with quotes removed, and its control operators as separate tokens: `a&&b;(c)` gives `a && b ; ( c )`.

    A newline outside quotes separates commands as `;` does, so it is kept as
    an operator; a backslash before it continues the line instead. Comments
    and heredoc bodies are not run as commands, so they are left out. shlex
    joins adjacent operators into one token, `;>` or `&&>`, so each run is
    split back into the operators it holds. A command shlex cannot read, such
    as `$'it\\'s'`, is split at operators and whitespace instead.
    """
    script = shell_source(command).replace("\\\n", " ")
    lexer = shlex.shlex(script, posix=True, punctuation_chars=OPERATOR_CHARS)
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        tokens = re.findall(r"[();<>|&`\n]+|[^\s();<>|&`]+", script)
    return [part for token in tokens for part in (OPERATOR.findall(token) if is_operator(token) else [token])]


HEREDOC = re.compile(r"<<(-?)[ \t]*\\?(['\"]?)([\w.-]+)\2")


def shell_source(command: str) -> str:
    """`command` without what the shell does not run as commands: `#` comments, and the body of each heredoc.

    A `<<` inside `((...))` or `$((...))` is a shift, not a heredoc. A heredoc
    whose closing line never comes keeps its body, so a missing delimiter
    cannot hide the lines after it.
    """
    kept = []
    pending = []
    quote = ""
    arithmetic = 0
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            kept.append(command[index : index + 2])
            index += 2
            continue
        if quote:
            if char == quote[-1]:
                quote = ""
        elif command.startswith("$'", index):
            quote = "$'"
            kept.append(quote)
            index += 2
            continue
        elif char in "'\"":
            quote = char
        elif char == "#" and (index == 0 or command[index - 1] in WORD_START):
            end = command.find("\n", index)
            index = len(command) if end == -1 else end
            continue
        elif command.startswith("((", index):
            arithmetic += 2
            kept.append("((")
            index += 2
            continue
        elif arithmetic and char in "()":
            arithmetic += 1 if char == "(" else -1
        elif char == "\n" and pending:
            kept.append(char)
            index = skip_heredoc_bodies(command, index + 1, pending)
            pending = []
            continue
        elif command.startswith("<<<", index):
            kept.append("<<<")
            index += 3
            continue
        elif char == "<" and not arithmetic and (match := HEREDOC.match(command, index)):
            pending.append((match.group(1) == "-", match.group(3)))
            kept.append(match.group(0))
            index = match.end()
            continue
        kept.append(char)
        index += 1
    return "".join(kept)


def skip_heredoc_bodies(command: str, index: int, pending: list) -> int:
    """The index just past the closing line of each heredoc in `pending`, read in order from `index`.

    Stops at the start of the first body whose closing line never comes.
    """
    for strip_tabs, delimiter in pending:
        position = index
        while position < len(command):
            end = command.find("\n", position)
            end = len(command) if end == -1 else end
            line = command[position:end]
            position = end + 1
            if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                index = min(position, len(command))
                break
        else:
            return index
    return index


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
    `bash -o pipefail -c`, `sh -lc`.
    """
    for index, word in enumerate(words[:-1]):
        if is_operator(word):
            return None
        if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", word):
            return words[index + 1]
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
