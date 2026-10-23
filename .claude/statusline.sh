#!/usr/bin/env bash
# Context-usage warning. Runs locally on every render and costs no API tokens.
#
# Why a status line and not a hook: no hook event carries context usage, and
# PreCompact — the only event that fires near the danger zone — arrives when
# compaction is already happening. A warning you get at compaction time is a
# notification, not a warning. This one is continuous.
#
# ⚠️ The thresholds below MUST stay under the auto-compact point (default ~97%).
# A warning at the auto-compact threshold fires simultaneously with the event
# it is meant to give you time to avoid.
set -uo pipefail

WARN=55   # start thinking about wrapping up
DANGER=65 # write the handoff and /clear now — 10 points of headroom to do it in

input=$(cat)
val() { printf '%s' "$input" | /usr/bin/python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: print(''); raise SystemExit
cur=d
for k in sys.argv[1].split('.'):
    cur = cur.get(k) if isinstance(cur, dict) else None
    if cur is None: break
print('' if cur is None else cur)" "$1" 2>/dev/null; }

MODEL=$(val model.display_name)
DIR=$(val workspace.current_dir)
PCT=$(val context_window.used_percentage)

BRANCH=$(git -C "${DIR:-$PWD}" branch --show-current 2>/dev/null)
DIRTY=''
[ -n "$(git -C "${DIR:-$PWD}" status --porcelain=v1 -uno 2>/dev/null)" ] && DIRTY='*'

R=$'\033[0m'; DIM=$'\033[2m'; AMBER=$'\033[33m'; RED=$'\033[1;31m'; GREEN=$'\033[32m'

# used_percentage is null before the first API call and again right after a
# /compact. Absent is absent — show a dash rather than a reassuring 0%.
if [ -z "$PCT" ]; then
  CTX="${DIM}ctx —${R}"
else
  P=${PCT%%.*}
  FILLED=$(( P / 5 )); [ "$FILLED" -gt 20 ] && FILLED=20
  BAR=$(printf '█%.0s' $(seq 1 $FILLED) 2>/dev/null)
  EMPTY=$(printf '░%.0s' $(seq 1 $(( 20 - FILLED ))) 2>/dev/null)
  if   [ "$P" -ge "$DANGER" ]; then CTX="${RED}${BAR}${EMPTY} ${P}% — handoff + /clear NOW${R}"
  elif [ "$P" -ge "$WARN" ];   then CTX="${AMBER}${BAR}${EMPTY} ${P}% — start wrapping up${R}"
  else                              CTX="${GREEN}${BAR}${EMPTY}${R} ${DIM}${P}%${R}"
  fi
fi

printf '%s%s%s %s%s%s%s%s\n%s\n' \
  "$DIM" "${MODEL:-claude}" "$R" \
  "$DIM" "${DIR##*/}" "$R" \
  "${BRANCH:+ ⎇ $BRANCH}" "$DIRTY" \
  "$CTX"
