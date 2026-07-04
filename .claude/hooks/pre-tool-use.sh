#!/usr/bin/env bash
#
# ARCHETYPE: COPY-AND-TWEAK — works as-is, but the `protected` list is yours to edit.
#
# PreToolUse hook for Edit|Write. Claude Code pipes the tool call to us as JSON
# on stdin; we pull the target path out of .tool_input.file_path. If that path
# matches anything in the `protected` array below, we print a reason to stderr
# and exit 2 — exit code 2 tells Claude Code to BLOCK the edit and hand our
# message back to Claude. Any other exit (0) lets the edit through.
#
# Requires `jq`. Registered under hooks.PreToolUse (matcher "Edit|Write") in
# .claude/settings.json — this script does nothing unless that registration exists.

set -euo pipefail

# ── PERSONALISE: paths/globs that must not be edited by Claude ────────────────
# Each entry is matched as a substring of the target file path. Seed examples:
protected=(
  "db/migrations/"
  "legacy/"
  ".env"
)
# ──────────────────────────────────────────────────────────────────────────────

input="$(cat)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"

# No path to check (or non-file tool) — nothing to protect, allow it.
[ -z "$file_path" ] && exit 0

for entry in "${protected[@]}"; do
  case "$file_path" in
    *"$entry"*)
      echo "Blocked: '$file_path' is protected (matched '$entry' in the pre-tool-use hook). Edit it by hand if you really mean to." >&2
      exit 2
      ;;
  esac
done

exit 0
