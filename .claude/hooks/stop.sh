#!/usr/bin/env bash
#
# Stop hook — runs when Claude Code finishes a turn.
#
# Default behaviour: nudge you that the turn is done (desktop notification on
# macOS, terminal bell everywhere). Reads the Stop event JSON on stdin but
# doesn't need anything from it for the default path.
#
# Registered under hooks.Stop in .claude/settings.json.

set -euo pipefail

cat >/dev/null   # drain stdin

# Desktop notification on macOS; fall back to a terminal bell elsewhere.
if command -v osascript >/dev/null 2>&1; then
  osascript -e 'display notification "Claude Code finished the turn." with title "Claude Code"' >/dev/null 2>&1 || printf '\a' >&2
else
  printf '\a' >&2
fi

# ── OPTIONAL: keep working until the tests pass ───────────────────────────────
# Uncomment this block to refuse to stop while your test command fails. Emitting
# {"decision":"block","reason":"..."} on stdout sends Claude back to work with
# that reason instead of ending the turn. Point TEST_CMD at your suite first.
# Leave it commented if you don't want an automatic test gate on every stop.
#
# TEST_CMD="npm test --silent"
# if ! output="$($TEST_CMD 2>&1)"; then
#   printf '{"decision":"block","reason":%s}\n' \
#     "$(printf 'Tests are failing — fix them before stopping:\n%s' "$output" | jq -Rs .)"
#   exit 0
# fi
# ──────────────────────────────────────────────────────────────────────────────

exit 0
