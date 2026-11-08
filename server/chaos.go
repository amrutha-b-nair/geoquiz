package main

// Chaos endpoints: ways to make this service misbehave on purpose, so you can
// practise finding the problem with Linux tools. They only exist when the
// server is started with CHAOS=1. Never turn this on for a real deployment.

import (
	"net/http"
	"os"
	"runtime"
	"runtime/debug"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

type chaos struct {
	mu      sync.Mutex
	files   []*os.File // file descriptors we "forgot" to close
	memory  [][]byte   // memory we hold on to
	latency atomic.Int64
}

var chaosState chaos

// extraLatency is added to every API request (set with /api/debug/chaos/slow).
func extraLatency() time.Duration { return time.Duration(chaosState.latency.Load()) }

func registerChaos(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/debug/chaos/leak-fds", chaosLeakFDs)
	mux.HandleFunc("POST /api/debug/chaos/alloc", chaosAlloc)
	mux.HandleFunc("POST /api/debug/chaos/cpu", chaosCPU)
	mux.HandleFunc("POST /api/debug/chaos/slow", chaosSlow)
	mux.HandleFunc("POST /api/debug/chaos/crash", chaosCrash)
	mux.HandleFunc("POST /api/debug/chaos/reset", chaosReset)
}

func intParam(r *http.Request, name string, def, max int) int {
	v, err := strconv.Atoi(r.URL.Query().Get(name))
	if err != nil || v < 0 {
		return def
	}
	if v > max {
		return max
	}
	return v
}

// leak-fds?n=100 opens n files and never closes them.
// Each open file uses one file descriptor; a process may only have `ulimit -n` of them.
func chaosLeakFDs(w http.ResponseWriter, r *http.Request) {
	n := intParam(r, "n", 100, 100000)
	chaosState.mu.Lock()
	defer chaosState.mu.Unlock()
	opened := 0
	for i := 0; i < n; i++ {
		f, err := os.Open("/dev/null")
		if err != nil {
			logger.Error("chaos: could not open more files", "opened", opened, "err", err)
			writeJSON(w, http.StatusInternalServerError, map[string]any{"opened": opened, "error": err.Error()})
			return
		}
		chaosState.files = append(chaosState.files, f)
		opened++
	}
	logger.Warn("chaos: leaked file descriptors", "opened", opened, "leaked_total", len(chaosState.files))
	writeJSON(w, http.StatusOK, map[string]any{"opened": opened, "leaked_total": len(chaosState.files)})
}

// alloc?mb=50 allocates memory and keeps it, like a cache that never evicts.
func chaosAlloc(w http.ResponseWriter, r *http.Request) {
	mb := intParam(r, "mb", 50, 4096)
	buf := make([]byte, mb<<20)
	// Touch every page: until memory is written, Linux doesn't really hand it
	// over, and it won't show up in RSS.
	for i := 0; i < len(buf); i += 4096 {
		buf[i] = 1
	}
	chaosState.mu.Lock()
	chaosState.memory = append(chaosState.memory, buf)
	held := 0
	for _, b := range chaosState.memory {
		held += len(b) >> 20
	}
	chaosState.mu.Unlock()
	logger.Warn("chaos: allocated memory", "mb", mb, "held_mb", held)
	writeJSON(w, http.StatusOK, map[string]any{"allocated_mb": mb, "held_mb": held})
}

// cpu?seconds=30&workers=2 keeps `workers` CPU cores busy for a while.
func chaosCPU(w http.ResponseWriter, r *http.Request) {
	secs := intParam(r, "seconds", 30, 600)
	workers := intParam(r, "workers", runtime.NumCPU(), 256)
	until := time.Now().Add(time.Duration(secs) * time.Second)
	for i := 0; i < workers; i++ {
		go func() {
			x := 0
			for time.Now().Before(until) {
				for j := 0; j < 1_000_000; j++ {
					x += j
				}
			}
			_ = x
		}()
	}
	logger.Warn("chaos: burning CPU", "seconds", secs, "workers", workers)
	writeJSON(w, http.StatusOK, map[string]any{"seconds": secs, "workers": workers})
}

// slow?ms=500 adds a delay to every API request (ms=0 turns it off).
func chaosSlow(w http.ResponseWriter, r *http.Request) {
	ms := intParam(r, "ms", 500, 30000) // capped below the server's 60s WriteTimeout
	chaosState.latency.Store(int64(time.Duration(ms) * time.Millisecond))
	logger.Warn("chaos: added latency to every request", "ms", ms)
	writeJSON(w, http.StatusOK, map[string]any{"latency_ms": ms})
}

// crash makes the process die with a panic, the way a real bug would.
// (A panic inside a request handler is caught by Go's HTTP server, so this one
// happens on a separate goroutine, which takes the whole process down.)
func chaosCrash(w http.ResponseWriter, r *http.Request) {
	logger.Error("chaos: crashing on purpose")
	writeJSON(w, http.StatusAccepted, map[string]any{"crashing": true})
	go func() {
		time.Sleep(100 * time.Millisecond) // let the response go out first
		panic("chaos: crash requested")
	}()
}

// reset undoes leak-fds, alloc and slow.
func chaosReset(w http.ResponseWriter, r *http.Request) {
	chaosState.mu.Lock()
	closed := len(chaosState.files)
	for _, f := range chaosState.files {
		f.Close()
	}
	chaosState.files = nil
	chaosState.memory = nil
	chaosState.mu.Unlock()
	chaosState.latency.Store(0)
	debug.FreeOSMemory() // hand freed memory back to the OS so RSS drops right away
	logger.Info("chaos: reset", "closed_fds", closed)
	writeJSON(w, http.StatusOK, map[string]any{"closed_fds": closed, "memory": "released", "latency_ms": 0})
}
