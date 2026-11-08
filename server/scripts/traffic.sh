#!/usr/bin/env bash
# Pretend to be players: sends a steady stream of requests to geoquiz-scores and
# prints one line per request (status, method, path, time). Stop with Ctrl+C.
#
#   ./traffic.sh                 # 5 requests/second against localhost:8080
#   RATE=20 ./traffic.sh         # 20 requests/second
#   BASE=http://10.0.0.5:8080 ./traffic.sh
set -uo pipefail

BASE="${BASE:-http://localhost:8080}"
RATE="${RATE:-5}"
names=(Asha Ben Chen Dara Eli Femi Gita Hugo Ines Jon Kofi Lena Mo Nia Omar Pia)
pause=$(awk "BEGIN { print 1 / $RATE }")

request() {
  local method=$1 path=$2 body=${3:-}
  local out
  if [[ $method == POST ]]; then
    out=$(curl -s -o /dev/null -m 5 -w '%{http_code} %{time_total}' -X POST \
      -H 'Content-Type: application/json' -d "$body" "$BASE$path")
  else
    out=$(curl -s -o /dev/null -m 5 -w '%{http_code} %{time_total}' "$BASE$path")
  fi
  local code=${out%% *} secs=${out##* }
  [[ $code == 000 ]] && code="ERR"   # no response at all: refused, timed out, reset...
  printf '%s %s  %-5s %-18s %ss\n' "$(date +%T)" "$code" "$method" "$path" "$secs"
}

echo "Sending ~$RATE req/s to $BASE (Ctrl+C to stop)"
while true; do
  r=$((RANDOM % 100))
  if (( r < 70 )); then
    request GET /api/leaderboard
  elif (( r < 90 )); then
    total=$((RANDOM % 25 + 1))
    request POST /api/scores "{\"name\":\"${names[RANDOM % ${#names[@]}]}\",\"score\":$((RANDOM % (total + 1))),\"total\":$total}"
  elif (( r < 95 )); then
    request POST /api/scores '{"name":"","score":5,"total":3}'   # a bad request on purpose (400)
  else
    request GET /api/healthz
  fi &
  sleep "$pause"
done
