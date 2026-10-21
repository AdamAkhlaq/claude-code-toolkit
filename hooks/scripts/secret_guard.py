"""PreToolUse hook for Bash.

On `git commit`, scans the lines being added for credential patterns and blocks
the commit on a hit. Reports the file, line and pattern name, never the match.
Paths matching `secretAllowlist` in `.claude/toolkit.json` are skipped.
"""

import re
import sys

from _common import (
    block,
    commits_all_tracked,
    first_match,
    git,
    is_git_commit,
    load_config,
    project_dir,
    read_event,
    tool_input,
)

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}\b")),
    ("bearer token", re.compile(r"(?i)\bauthorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("assigned secret", re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret|password|passwd|auth[_-]?token|access[_-]?token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
]

PLACEHOLDER = re.compile(r"(?i)\b(?:example|placeholder|changeme|your[_-]?|xxx+|dummy|redacted|<[^>]+>)")


def added_lines(root, include_unstaged: bool):
    args = ["diff", "--unified=0", "--no-color", "--no-ext-diff"]
    args.append("HEAD" if include_unstaged else "--cached")
    diff = git(root, *args)
    if diff is None:
        return []
    current = None
    line_no = 0
    found = []
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            current = raw[4:]
            current = current[2:] if current.startswith("b/") else current
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            line_no = int(match.group(1)) if match else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            if current and current != "/dev/null":
                found.append((current, line_no, raw[1:]))
            line_no += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            continue
    return found


def main() -> int:
    root = project_dir()
    config = load_config(root)
    if config is None:
        return 0
    command = tool_input(read_event()).get("command") or ""
    if not is_git_commit(command):
        return 0
    allowlist = config.get("secretAllowlist") or []
    hits = []
    for path, line_no, text in added_lines(root, commits_all_tracked(command)):
        if first_match(path, allowlist):
            continue
        if PLACEHOLDER.search(text):
            continue
        for name, pattern in PATTERNS:
            if pattern.search(text):
                hits.append(f"  {path}:{line_no}  looks like a {name}")
                break
    if not hits:
        return 0
    listing = "\n".join(hits[:20])
    more = f"\n  ... and {len(hits) - 20} more" if len(hits) > 20 else ""
    return block(
        "Blocked: the commit would add what looks like a credential.\n"
        f"{listing}{more}\n"
        "Move secrets to the environment or a secret store, unstage the file, and commit again. "
        "If this is test data, add the path to secretAllowlist in .claude/toolkit.json."
    )


if __name__ == "__main__":
    sys.exit(main())
