#!/usr/bin/env bash
# Mystery incident: secretly breaks geoquiz-scores in one of several ways.
# Your job: find out what's wrong using only Linux tools, logs and the service itself.
# (Don't read the scenarios below before you've played a few times!)
#
#   ./mystery.sh            start a random incident
#   ./mystery.sh reveal     show what it was (after you've written down your diagnosis)
#   ./mystery.sh cleanup    undo everything and restart the service
#
# Needs the service installed with install.sh (systemd unit "geoquiz-scores", CHAOS=1),
# and sudo for some scenarios.
set -uo pipefail

BASE="${BASE:-http://localhost:8080}"
UNIT=geoquiz-scores
DATA=/var/lib/geoquiz-scores/scores.jsonl
ANSWER="$HOME/.geoquiz-mystery"

chaos() { curl -fsS -m 5 -X POST "$BASE/api/debug/chaos/$1" >/dev/null; }
save_answer() { echo "$1" | base64 > "$ANSWER"; }   # base64 so a glance doesn't spoil it

case "${1:-start}" in
reveal)
  [[ -f $ANSWER ]] || { echo "No mystery running."; exit 1; }
  echo "It was: $(base64 -d "$ANSWER")"
  exit 0
  ;;
cleanup)
  echo "Cleaning up..."
  pkill -f 'geoquiz-mystery-memory' 2>/dev/null
  pkill -f 'http.server 8080' 2>/dev/null
  [[ -f $DATA ]] && sudo chown geoquiz:geoquiz "$DATA" && sudo chmod 644 "$DATA"
  chaos reset 2>/dev/null
  sudo systemctl reset-failed "$UNIT" 2>/dev/null
  sudo systemctl restart "$UNIT"
  sleep 1
  curl -fsS "$BASE/api/healthz" && echo && echo "All clear."
  rm -f "$ANSWER"
  exit 0
  ;;
start) ;;
*) echo "usage: $0 [start|reveal|cleanup]"; exit 2 ;;
esac

if [[ -f $ANSWER ]]; then
  echo "A mystery is already running. Use '$0 reveal' or '$0 cleanup' first."
  exit 1
fi
systemctl is-active --quiet "$UNIT" || { echo "$UNIT isn't running; start it first."; exit 1; }
sudo -v || exit 1   # ask for the sudo password now, so it doesn't give the game away later

scenario=$((RANDOM % 7))
case $scenario in
0)
  save_answer "File descriptor leak: the process opened files and never closed them, until it hit LimitNOFILE (512). New connections can't be accepted. Clues: 'too many open files' in journalctl, ls /proc/PID/fd | wc -l, lsof -p PID. Fix: restart (and in real life, find the leak)."
  chaos "leak-fds?n=600" 2>/dev/null
  ;;
1)
  save_answer "Memory leak: the process grew ~40 MB every few seconds until the kernel OOM-killed it (MemoryMax=300M), then systemd restarted it, and it happened again. Clues: RSS growing in top/ps, 'oom-kill' in systemctl status, journalctl -k / dmesg, NRestarts going up."
  # A background loop that keeps 'leaking' (named so cleanup can find it).
  # The trailing comment is part of the command line, so cleanup can find it with pkill -f.
  nohup bash -c "while true; do curl -s -m 5 -X POST '$BASE/api/debug/chaos/alloc?mb=40' >/dev/null; sleep 3; done # geoquiz-mystery-memory" >/dev/null 2>&1 &
  ;;
2)
  save_answer "CPU saturation: every core was kept busy for 10 minutes, so requests got slower. Clues: top shows geoquiz-scores near 100% x cores, load average high, curl -w '%{time_total}' slower; uptime / vmstat 1 (r column)."
  chaos "cpu?seconds=600&workers=$(( $(nproc) * 2 ))"
  ;;
3)
  save_answer "Added latency: every API request waits 3 seconds before being handled. CPU, memory and FDs all look fine, which is the clue. Clues: curl -w '%{time_total}', duration_ms in the logs, strace shows the threads mostly idle (futex/epoll waits)."
  chaos "slow?ms=3000"
  ;;
4)
  save_answer "Crash loop: the process crashed (panic) repeatedly until systemd gave up (start-limit-hit). Clues: systemctl status says failed / start-limit-hit, journalctl shows 'panic: chaos: crash requested' and stack traces, NRestarts. Fix: systemctl reset-failed + start (and in real life, fix the bug)."
  for _ in 1 2 3 4 5 6; do
    chaos crash 2>/dev/null
    sleep 3   # RestartSec=2, so it's back up by now
  done
  ;;
5)
  save_answer "Port already in use: someone else's process (a python http.server) grabbed port 8080 while the service was restarting, so geoquiz-scores can't start ('address already in use'). Clues: journalctl, ss -tlnp | grep 8080 shows python, not geoquiz-scores. Fix: stop the other process, then start the service."
  sudo systemctl stop "$UNIT"
  nohup python3 -m http.server 8080 --bind 0.0.0.0 >/dev/null 2>&1 &
  sleep 1
  sudo systemctl start "$UNIT" 2>/dev/null
  ;;
6)
  save_answer "Bad file permissions: the data file was made owned by root and unreadable, so after a restart the service (running as user 'geoquiz') can't open it and keeps failing. Clues: journalctl shows 'permission denied', ls -l /var/lib/geoquiz-scores, systemctl show -p User. Fix: chown geoquiz:geoquiz the file."
  sudo touch "$DATA"
  sudo chown root:root "$DATA"
  sudo chmod 600 "$DATA"
  sudo systemctl restart "$UNIT"
  ;;
esac

cat <<'EOF'

🚨 PAGE: geoquiz-scores is unhealthy. Users are reporting problems.

Investigate like an on-call engineer:
  1. What do users see?          curl -v / the browser / traffic.sh
  2. Is the service running?     systemctl status geoquiz-scores
  3. What do the logs say?       journalctl -u geoquiz-scores --since "10 min ago"
  4. What's the process doing?   top, ps, /proc/PID/..., lsof, ss, strace
  5. Write down: symptom, cause, evidence, fix. Then fix it.

When done:  ./mystery.sh reveal   then   ./mystery.sh cleanup
EOF
