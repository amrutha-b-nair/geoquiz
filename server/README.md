# geoquiz-scores

The leaderboard API for GeoQuiz, and the service you learn to operate in the SRE course
([`docs/sre/`](../docs/sre/)). It's written in Go using only the standard library, and it stores scores in
a plain file, `scores.jsonl`, with one JSON object per line.

## Run it

You need Go 1.22 or newer.

```bash
cd server
go build -o geoquiz-scores .
CHAOS=1 ./geoquiz-scores
```

Open http://localhost:8080. The server also serves the GeoQuiz frontend from `../web`, so the
game and the API come from the same address. At the end of a quiz you can save your score, and you'll
see the leaderboard. Logs (one JSON line per request) are written to your terminal.

On GitHub Pages there's no backend, so the leaderboard simply doesn't appear. The server tells the page
it's there by setting a `geoquiz_api` cookie.

## API

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/healthz` | `200 {"status":"ok"}` if the instance looks healthy, `503` if not |
| `GET` | `/api/leaderboard?limit=10` | Best scores, highest percentage first |
| `POST` | `/api/scores` | Body `{"name":"Asha","score":8,"total":10}` → `201`, or `400` with `{"error":...}` |

```bash
curl localhost:8080/api/healthz
curl -X POST localhost:8080/api/scores -d '{"name":"Asha","score":8,"total":10}'
curl localhost:8080/api/leaderboard
```

## Configuration

Set with environment variables:

| Variable | Default | |
|---|---|---|
| `ADDR` | `:8080` | Address to listen on |
| `DATA_DIR` | `./data` | Where `scores.jsonl` is kept |
| `WEB_DIR` | `../web` | Frontend to serve at `/`; empty = API only |
| `CHAOS` | off | `1` enables the chaos endpoints below. **Practice only.** |

## Signals

| Signal | Effect |
|---|---|
| `SIGTERM`, `SIGINT` (Ctrl+C) | Graceful shutdown: stop accepting, finish requests in flight (up to 10s), exit 0 |
| `SIGHUP` | Log a status line: pid, uptime, scores, goroutines, open file descriptors, memory |

## Chaos endpoints (`CHAOS=1` only)

| `POST` | Effect |
|---|---|
| `/api/debug/chaos/leak-fds?n=100` | Open `n` files and never close them |
| `/api/debug/chaos/alloc?mb=50` | Allocate memory and keep it |
| `/api/debug/chaos/cpu?seconds=30&workers=2` | Keep `workers` cores busy |
| `/api/debug/chaos/slow?ms=500` | Add a delay to every API request (`ms=0` turns it off) |
| `/api/debug/chaos/crash` | Crash the process with a panic |
| `/api/debug/chaos/reset` | Undo leak-fds, alloc and slow |

## Scripts

- `scripts/install.sh`: build and install as a systemd service (`geoquiz-scores`)
- `scripts/traffic.sh`: simulated players; `RATE=20 ./scripts/traffic.sh`
- `scripts/mystery.sh`: secretly breaks the service so you can practise being on call

## Tests

```bash
go vet ./... && go test ./...
```
