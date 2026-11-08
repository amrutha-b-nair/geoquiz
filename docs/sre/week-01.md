# Week 1: How a Machine Actually Works

**Goal:** by the end of the week, when someone says "the service is broken", you can find out *why*
using only a Linux shell. Is it dead, stuck, out of memory, out of file descriptors, out of disk, out of
CPU, or just slow?

**The service:** [`server/`](../../server/) (`geoquiz-scores`), the GeoQuiz leaderboard API, written in Go. It
has built-in "chaos" switches so you can break it on purpose.

**Time:** about 10–12 hours. The plan below spreads it over 7 days, but go at your own pace.

| Day | Topic | Read | Do |
|---|---|---|---|
| 0 | Setup | – | Get a Linux machine and tools |
| 1 | What SRE is | SRE book ch. 1–3 | Run the service, play, read its logs |
| 2 | Processes, `/proc`, signals | proc(5), signal(7) | Inspect and signal the process |
| 3 | systemd and journald | systemd.service | Run it as a real service |
| 4 | Observing a machine | SRE book ch. 4–6, Netflix 60s | Tool tour under load |
| 5–6 | Breaking things | – | Labs A–E |
| 7 | On call | – | Mystery incidents + write-ups |

Keep a **journal** (a plain text file is fine). For every lab, write down: *what I did → what I saw → what
it means*. You'll reuse it in interviews.

---

## Reading list

**SRE mindset** ([*Site Reliability Engineering*](https://sre.google/sre-book/table-of-contents/), free online):
- Ch. 1 [Introduction](https://sre.google/sre-book/introduction/)
- Ch. 2 [The Production Environment at Google](https://sre.google/sre-book/production-environment/): skim it, but notice how much is about machines, jobs and scheduling.
- Ch. 3 [Embracing Risk](https://sre.google/sre-book/embracing-risk/): error budgets, the core idea of SRE.
- Ch. 4 [Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- Ch. 5 [Eliminating Toil](https://sre.google/sre-book/eliminating-toil/)
- Ch. 6 [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/): the "four golden signals".

**Linux:**
- [Linux Performance Analysis in 60,000 Milliseconds](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) (Netflix). You'll use this checklist on Day 4.
- [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html). Look at the "Linux observability tools" diagram and keep it open as a map.
- Julia Evans: [strace zine](https://jvns.ca/blog/2015/04/14/strace-zine/) and [Linux debugging tools you'll love](https://jvns.ca/blog/2016/09/07/new-zine-linux-debugging-tools-youll-love/). Short, friendly, very good.
- Man pages, for reference rather than reading cover to cover: [proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html),
  [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html),
  [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html),
  [systemd.resource-control](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).

---

## Day 0: Setup

### A Linux machine

This week needs **real Linux with systemd**: `/proc`, `strace` and systemd don't exist on macOS. Pick one:

- **Mac:** an Ubuntu VM with [Multipass](https://canonical.com/multipass/install) (`multipass launch --name sre --cpus 2 --memory 2G --disk 10G`, then `multipass shell sre`), or OrbStack/UTM.
- **Windows:** WSL2 with Ubuntu, and [turn systemd on](https://learn.microsoft.com/en-us/windows/wsl/systemd).
- **Linux:** you're set. A VM is still nice, so you can break it without worrying.
- Or a $4–6/month cloud VM. That's realistic, but turn it off when you're done.

Ubuntu 22.04 or newer is assumed below.

### Tools

```bash
sudo apt update
sudo apt install -y git curl jq htop strace lsof sysstat psmisc procps iproute2 python3
```

Install Go 1.22 or newer from [go.dev/doc/install](https://go.dev/doc/install) (Ubuntu's `golang-go` package may be too old),
then check `go version`.

### The code

```bash
git clone https://github.com/amrutha-b-nair/geoquiz.git
cd geoquiz/server
go test ./...
```

---

## Day 1: What SRE is, and meeting the service

**Read:** SRE book ch. 1–3. Write down, in your own words:
1. What's the difference between an SRE and an ops/sysadmin team?
2. What is an error budget, and why is 100% reliability the wrong target?
3. What is toil? List three things you've done at work that were toil.

**Do:** run the service in the foreground.

```bash
cd server
go build -o geoquiz-scores .
CHAOS=1 ./geoquiz-scores
```

Open http://localhost:8080 (on a VM, use the VM's IP: `hostname -I`). Play a quiz and save your score.
Watch the terminal: **every request you made is a log line.** That's the frontend's job here. It's a
realistic source of traffic and log lines. You don't *need* it, though: most traffic in this course comes
from `traffic.sh`.

In a second terminal:

```bash
curl -v localhost:8080/api/healthz              # -v shows the request and response headers
curl -X POST localhost:8080/api/scores -d '{"name":"me","score":3,"total":10}'
curl -X POST localhost:8080/api/scores -d '{"name":"me","score":30,"total":10}'   # invalid
curl -s localhost:8080/api/leaderboard | jq
./scripts/traffic.sh                             # simulated players, Ctrl+C to stop
```

Logs are JSON so that machines can query them. Try it:

```bash
./geoquiz-scores 2>&1 | jq -c 'select(.status >= 400)'            # only failed requests
./geoquiz-scores 2>&1 | jq -r '[.status, .path, .duration_ms] | @tsv'
```

**Questions:**
- Where are scores stored? Look at `data/scores.jsonl` with `tail -f` while saving scores.
- Restart the server. Are the scores still there? Why?
- What's the difference between a 400 and a 500, from an SRE's point of view? Which one should wake someone up?

---

## Day 2: Processes, `/proc` and signals

Keep the server running in terminal 1 (`CHAOS=1 ./geoquiz-scores`), and `./scripts/traffic.sh` in terminal 2. Work in terminal 3.

### Find the process

```bash
pgrep -a geoquiz                      # PID and command line
PID=$(pgrep -f '^./geoquiz-scores')
ps -o pid,ppid,user,stat,%cpu,%mem,rss,vsz,nlwp,etime,cmd -p $PID
pstree -p -s $PID                     # its parents, and its threads in {braces}
```

Look up every `ps` column in `man ps`. In particular, find out:
- **RSS vs VSZ:** why is VSZ so much bigger? Which one is "real" memory use?
- **NLWP:** why does a Go program have several threads?
- **STAT:** what do `S`, `R`, `D`, `T` and `Z` mean?

### Look inside it with `/proc`

Everything `ps` and `top` show comes from files under `/proc/<PID>/`. Read them directly:

```bash
cat /proc/$PID/status | head -30        # name, state, memory (VmRSS), threads
tr '\0' ' ' < /proc/$PID/cmdline; echo  # exact command line
tr '\0' '\n' < /proc/$PID/environ       # its environment. Notice CHAOS=1.
cat /proc/$PID/limits                   # "Max open files" etc.
ls -l /proc/$PID/fd                     # every open file and socket
readlink /proc/$PID/cwd /proc/$PID/exe
```

- In `fd/`, find `scores.jsonl`. What are `0`, `1` and `2`? What are the `socket:[...]` entries?
- `environ` lists environment variables. Who else on this machine can read it? (`ls -l /proc/$PID/environ`.) Why does this matter for secrets?

### Network: what's listening, and who's connected

```bash
ss -tlnp | grep 8080                    # listening sockets (-t tcp, -l listening, -n numeric, -p process)
ss -tnp | grep 8080                     # live connections; run traffic.sh to see them
curl -s localhost:8080/api/healthz      # now try to start a second copy in another terminal:
./geoquiz-scores                        # -> "address already in use". Read the log line.
```

### Watch system calls with strace

A program talks to the kernel through **system calls**. `strace` shows them live:

```bash
sudo strace -f -p $PID -e trace=accept4,read,write,fsync,openat -s 120
# in another terminal:
curl -X POST localhost:8080/api/scores -d '{"name":"strace","score":1,"total":1}'
```

Find the `accept4` (new connection), the `read` (the HTTP request arriving), the `write` to the scores file,
the `fsync`, and the `write` of the HTTP response. **This is the whole request, as the kernel sees it.**

### Signals

```bash
kill -HUP $PID       # this service logs a status line on SIGHUP. Check terminal 1.
kill -STOP $PID      # freeze it
curl -m 3 localhost:8080/api/healthz; ps -o stat -p $PID    # what happens? what's STAT now?
kill -CONT $PID      # unfreeze. Did the waiting curl requests get answered?
kill -TERM $PID      # graceful shutdown: read the last log lines
```

Start it again, then:

```bash
kill -KILL $PID      # (-9) no log lines this time. Why not?
```

Back in terminal 1, run `echo $?` after each of these. You'll see **0** after SIGTERM and **137** after SIGKILL. 137 = 128 + 9,
the signal number. You'll see exit codes like this in Kubernetes ("exit code 137") in week 7.

**Questions:**
- Why can a program catch SIGTERM but not SIGKILL? Why does that make SIGTERM the polite default?
- What does "graceful shutdown" protect against? (Hint: requests in flight during a deploy.)
- Read `main.go`: find where SIGTERM, SIGINT and SIGHUP are handled.

---

## Day 3: systemd and journald

Running a server in a terminal is fine for development. In production, something has to start it at boot, restart
it when it crashes, collect its logs and limit its resources. On most Linux machines that's **systemd**.

### Install it by hand (once)

Read [`server/deploy/geoquiz-scores.service`](../../server/deploy/geoquiz-scores.service) first. Every line has a comment. Then:

```bash
cd server && go build -o geoquiz-scores .
sudo useradd --system --no-create-home --shell /usr/sbin/nologin geoquiz   # a user just for the service
sudo install -m 0755 geoquiz-scores /usr/local/bin/
sudo mkdir -p /opt/geoquiz && sudo cp -r ../web /opt/geoquiz/web
sudo cp deploy/geoquiz-scores.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now geoquiz-scores
systemctl status geoquiz-scores
```

After this, `./scripts/install.sh` does all of it for you when you change the code.

Why a separate `geoquiz` user? `ps -o user -p $(systemctl show -p MainPID --value geoquiz-scores)`. If the
service gets hacked, the attacker is `geoquiz`, not you or root.

### Driving systemd

```bash
systemctl status geoquiz-scores                       # state, PID, memory, last log lines
systemctl cat geoquiz-scores                          # the unit file actually in use
systemctl show geoquiz-scores -p MainPID,NRestarts,MemoryCurrent,LimitNOFILE,User
sudo systemctl restart geoquiz-scores                 # stop (SIGTERM) + start
sudo systemctl edit geoquiz-scores                    # override settings without editing the original
systemd-cgls -u geoquiz-scores.service                # its processes (cgroup)
systemd-cgtop                                         # live CPU/memory per service
```

### Logs with journalctl

stdout of a systemd service goes to the **journal**:

```bash
journalctl -u geoquiz-scores -f                       # follow (like tail -f)
journalctl -u geoquiz-scores --since "10 min ago"
journalctl -u geoquiz-scores -p err                   # only errors
journalctl -u geoquiz-scores -o cat | jq -c 'select(.status >= 500)'
journalctl -u geoquiz-scores -b                       # since the last boot
journalctl -k                                         # kernel messages (OOM kills show up here)
```

### Check

- Reboot the VM (`sudo reboot`). Does the service come back on its own? Which line in the unit does that?
- Find the scores file now: `/var/lib/geoquiz-scores/`. Which unit setting created that directory?
- Run `traffic.sh` and `journalctl -f` side by side for a minute. That's what "watching a service" looks like before dashboards (week 4).

---

## Day 4: Observing a machine

**Read:** SRE book ch. 4–6 and the Netflix "60,000 milliseconds" article.

**Do:** run `RATE=20 ./scripts/traffic.sh` and go through the Netflix checklist on your machine. For **each**
command, write one line in your journal saying what the important columns mean and what's normal right now.
That's your **baseline**. On Day 5 you'll compare against it.

```bash
uptime                    # load averages: 1, 5, 15 minutes. Compare with `nproc`.
dmesg -T | tail           # recent kernel messages (OOM, disk errors, network)
vmstat 1                  # r = runnable processes, si/so = swapping, us/sy/id/wa = CPU split
mpstat -P ALL 1           # per-CPU usage: is one core pegged?
pidstat 1                 # CPU per process
iostat -xz 1              # disk: %util, await (latency)
free -m                   # memory. Read "available", not "free".
sar -n DEV 1              # network throughput per interface
sar -n TCP,ETCP 1         # new connections/s, retransmits
top                       # or htop. Press 1 for per-CPU, M to sort by memory, H for threads.
df -h; df -i              # disk space, and inodes (the number of files)
```

The **USE method** ties these together. For each resource (CPU, memory, disk, network, file descriptors),
check **U**tilization, **S**aturation (work queued up) and **E**rrors. Write a small table for your machine:
which command shows U, S and E for each resource?

---

## Day 5–6: Break it (labs A–E)

For every lab: start `traffic.sh` and `journalctl -u geoquiz-scores -f` first. **Before** you look at the
hints, try to diagnose it like you don't know what you did. Then write it up: *symptom → evidence → cause → fix*.

Handy shortcuts:

```bash
PID=$(systemctl show -p MainPID --value geoquiz-scores)
chaos() { curl -s -X POST "localhost:8080/api/debug/chaos/$1"; echo; }
```

### Lab A: crash loop

```bash
chaos crash
systemctl status geoquiz-scores      # what did systemd do? new PID?
systemctl show -p NRestarts geoquiz-scores
journalctl -u geoquiz-scores -n 40   # find the panic and the stack trace
```

Now crash it 6 times in a row, about 3 seconds apart (`for i in 1 2 3 4 5 6; do chaos crash; sleep 3; done`).
- What does `systemctl status` say now? Find `start-limit-hit`. Which unit lines caused it?
- Recover: `sudo systemctl reset-failed geoquiz-scores && sudo systemctl start geoquiz-scores`.
- Compare: `sudo kill -TERM $PID` vs `sudo kill -KILL $PID`. Which one gets restarted, and why? (Look up `Restart=on-failure`.)

**Lesson:** auto-restart hides crashes. A service can look "up" while crashing every minute. That's
why you track restarts (NRestarts here, restart count in Kubernetes).

### Lab B: file descriptor leak

Every open file **and every network connection** uses a file descriptor (fd). There's a limit per process.

```bash
grep "open files" /proc/$PID/limits       # 512, from LimitNOFILE in the unit
ls /proc/$PID/fd | wc -l                  # normal count
chaos "leak-fds?n=600"
curl -m 5 localhost:8080/api/healthz      # what happens?
```

Diagnose it:

```bash
ls /proc/$PID/fd | wc -l
sudo lsof -p $PID | awk '{print $NF}' | sort | uniq -c | sort -rn | head    # what's open, most common first
journalctl -u geoquiz-scores -n 20        # find "too many open files"
```

Fix: `chaos reset` (or restart the service).

- Why does `healthz` hang rather than return an error? (Hint: what does the server need to *accept* a connection?)
- Go raises its own soft limit to the hard limit at startup, which is why we set `LimitNOFILE` in the unit
  to make this lab possible. What's the default on your machine? Run `ulimit -n` and `ulimit -Hn`.

### Lab C: out of memory

```bash
systemctl show -p MemoryMax,MemoryCurrent geoquiz-scores
chaos "alloc?mb=100"; ps -o rss= -p $PID       # RSS in KB. Repeat a few times...
```

Somewhere past 300 MB the kernel kills it.

```bash
systemctl status geoquiz-scores       # look for "oom-kill" and status=9/KILL
journalctl -k | grep -i -A3 oom       # the kernel's own report
journalctl -u geoquiz-scores -n 30    # did the app log anything before dying? Why not?
```

- Are the saved scores still there after the restart? Why? (Memory vs disk.)
- Why did systemd OOM-kill this *service* rather than the whole machine running out? (`MemoryMax`, cgroups.)
- What would happen without `MemoryMax`? (Answer in words; don't try it on your laptop.)

### Lab D: disk full

Fill a *small, separate* disk so you don't fill your real one:

```bash
sudo fallocate -l 20M /var/tmp/geoquiz-small.img
sudo mkfs.ext4 -q /var/tmp/geoquiz-small.img
sudo mkdir -p /mnt/geoquiz-small
sudo mount -o loop /var/tmp/geoquiz-small.img /mnt/geoquiz-small
sudo chown geoquiz:geoquiz /mnt/geoquiz-small
sudo systemctl edit geoquiz-scores
#   add these two lines in the editor, save and quit:
#   [Service]
#   Environment=DATA_DIR=/mnt/geoquiz-small
sudo systemctl restart geoquiz-scores
df -h /mnt/geoquiz-small
```

Now fill it up and watch:

```bash
sudo dd if=/dev/zero of=/mnt/geoquiz-small/junk bs=1M     # stops at "No space left on device"
df -h /mnt/geoquiz-small
```

- Run `traffic.sh` or save a score in the browser. What do users see? What's in the log?
- Check `curl localhost:8080/api/healthz`. **It still says `ok`.** The health check is lying: the
  service can't do its main job, yet it reports healthy. Read the comment above `healthz` in `server/api.go`.
  How would you fix it? Write your idea down; you'll improve health checks in later weeks.
- Find what's using the space: `sudo du -sh /mnt/geoquiz-small/* | sort -h`.

**Twist: deleted but not gone.**

```bash
sudo rm /mnt/geoquiz-small/junk
sudo bash -c 'exec 3>/mnt/geoquiz-small/app.log; dd if=/dev/zero bs=1M count=15 >&3 2>/dev/null; sleep 900' &
sudo rm /mnt/geoquiz-small/app.log
df -h /mnt/geoquiz-small          # still full?!
sudo du -sh /mnt/geoquiz-small    # ...but du says it's empty
sudo lsof +L1                     # open files with 0 links = deleted but still open
```

A file's space is only freed when **nobody has it open**. Kill the `sleep` process holding it (`sudo kill <PID from lsof>`) and check `df` again.
This happens in real life with log files that get deleted while the app is still writing to them.

Clean up:

```bash
sudo systemctl revert geoquiz-scores && sudo systemctl restart geoquiz-scores
sudo umount /mnt/geoquiz-small && sudo rm /var/tmp/geoquiz-small.img
```

**Bonus, inodes:** on a fresh small disk, create thousands of empty files
(`for i in $(seq 6000); do sudo touch /mnt/geoquiz-small/f$i; done`) until it fails, then compare `df -h` with `df -i`.

### Lab E: slow (CPU, then latency)

**CPU:**

```bash
curl -s -o /dev/null -w '%{time_total}\n' localhost:8080/api/leaderboard     # baseline time
chaos "cpu?seconds=120&workers=$(( $(nproc) * 2 ))"
```

Within those 2 minutes: `uptime`, `top` (press `H` to see the threads), `vmstat 1` (look at `r` and `us`), `pidstat -p $PID 1`.
Time the curl again. Compare everything with your Day 4 baseline.

**Latency, with nothing obviously wrong:**

```bash
chaos "slow?ms=1500"
```

CPU, memory, fds and disk all look normal, yet every API call takes 1.5s+. How do you prove where the time goes?
- `curl -w` shows the total; `duration_ms` in the logs shows it's spent *inside* the server.
- `sudo strace -f -p $PID` shows the threads mostly waiting (`futex`, `epoll_pwait`), so it isn't CPU.
- In real systems this is usually waiting on something else: a slow database, DNS or an upstream API. You'll get
  proper tools for this (tracing) in week 4.

`chaos "slow?ms=0"` to undo.

---

## Day 7: On call (mystery incidents)

`mystery.sh` secretly breaks the service in one of 7 ways (some covered above, some new). You get a page
and have to figure it out.

```bash
cd server/scripts
./traffic.sh                # in one terminal, so there's traffic to break
./mystery.sh                # in another
```

Rules: no reading `mystery.sh`, and use only the tools from this week. For each incident, write a
**mini postmortem** in your journal:

```
Time to detect:   (when did you notice?)
Time to diagnose:
Symptom:          what users saw
Evidence:         the commands and output that proved the cause
Cause:
Fix:              what you did now
Prevent:          what would stop it happening again, or catch it sooner
```

Then `./mystery.sh reveal`, compare with your answer, and `./mystery.sh cleanup`. Do at least 3, and repeat
until you've seen all 7 kinds. Try to get faster each time.

---

## End-of-week self-check

You're ready for week 2 if you can answer these without looking anything up:

- [ ] Given a PID, find its memory use, thread count, open files, limits and listening ports.
- [ ] Explain RSS vs VSZ, and "free" vs "available" memory.
- [ ] Explain SIGTERM vs SIGKILL vs SIGHUP, and what exit code 137 means.
- [ ] Install, start, stop, enable, override and read the logs of a systemd service.
- [ ] Tell from `systemctl status` and the journal whether a service crashed, was OOM-killed, or hit its start limit.
- [ ] Explain why a disk can be full when `du` says it isn't.
- [ ] Explain why a health check can say "ok" while users get errors.
- [ ] Run the 60-second checklist and say which resource is the bottleneck.
- [ ] Explain an error budget to a backend engineer in two sentences.

**Next week:** networking: DNS, TCP, TLS, HTTP, and putting nginx in front of two copies of this service.
