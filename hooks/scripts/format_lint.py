"""PostToolUse hook for Edit, Write and MultiEdit.

Runs the formatters and then the linters configured in `.claude/toolkit.json`
for the file that just changed. Silent on success. On failure, prints the tool
output and exits 2 so Claude sees it and fixes it.

Config shape, each a map from glob to a command with a `{file}` placeholder:

    "formatters": { "*.{ts,tsx,js,json,md}": "npx prettier --write {file}" },
    "linters":    { "*.{ts,tsx}": "npx eslint {file}" }
"""

import shlex
import subprocess
import sys
from pathlib import Path

from _common import first_match, load_config, project_dir, read_event, target_path

TIMEOUT_SECONDS = 120
MAX_OUTPUT_LINES = 40


def expand_braces(pattern: str):
    """Turn `*.{ts,js}` into `*.ts` and `*.js`. One level is enough."""
    start = pattern.find("{")
    end = pattern.find("}", start)
    if start == -1 or end == -1:
        return [pattern]
    head, body, tail = pattern[:start], pattern[start + 1 : end], pattern[end + 1 :]
    return [head + option.strip() + tail for option in body.split(",")]


def matching_commands(rel: str, table) -> list:
    if not isinstance(table, dict):
        return []
    commands = []
    for pattern, command in table.items():
        if not isinstance(command, str) or not command.strip():
            continue
        if first_match(rel, expand_braces(pattern)):
            commands.append(command)
    return commands


def run(command: str, path: Path, root: Path):
    rendered = command.replace("{file}", shlex.quote(str(path)))
    try:
        result = subprocess.run(
            rendered,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return rendered, f"timed out after {TIMEOUT_SECONDS}s"
    except OSError as exc:
        return rendered, str(exc)
    if result.returncode == 0:
        return rendered, None
    output = (result.stdout + result.stderr).strip().splitlines()
    tail = output[-MAX_OUTPUT_LINES:]
    if len(output) > MAX_OUTPUT_LINES:
        tail.insert(0, f"... ({len(output) - MAX_OUTPUT_LINES} earlier lines omitted)")
    return rendered, "\n".join(tail) or f"exit code {result.returncode}"


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    rel = target_path(read_event(), root)
    if not rel:
        return 0
    path = root / rel
    if not path.is_file():
        return 0
    failures = []
    for stage in ("formatters", "linters"):
        for command in matching_commands(rel, config.get(stage)):
            rendered, error = run(command, path, root)
            if error:
                failures.append(f"{stage[:-1]} failed for {rel}\n  $ {rendered}\n{error}")
    if not failures:
        return 0
    print("\n\n".join(failures), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
