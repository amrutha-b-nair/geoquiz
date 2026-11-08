// geoquiz-scores is the leaderboard API for GeoQuiz, and the service you learn
// to operate in the SRE course (see docs/sre/). It uses only Go's standard library.
//
// Configuration (environment variables):
//
//	ADDR      address to listen on            (default ":8080")
//	DATA_DIR  where scores.jsonl is kept      (default "./data")
//	WEB_DIR   GeoQuiz frontend to serve at /  (default "../web"; set to "" to serve the API only)
//	CHAOS     "1" enables /api/debug/chaos/*  (default off; for practice only)
package main

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"
)

// Logs go to stdout as one JSON object per line. Under systemd they end up in
// the journal (journalctl -u geoquiz-scores); in week 4 they get shipped to Loki.
var logger = slog.New(slog.NewJSONHandler(os.Stdout, nil))

var started = time.Now()

func env(key, def string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return def
}

func main() {
	addr := env("ADDR", ":8080")
	dataDir := env("DATA_DIR", "./data")
	webDir := env("WEB_DIR", "../web")
	chaosOn := env("CHAOS", "") == "1"

	store, err := OpenStore(dataDir)
	if err != nil {
		logger.Error("could not open data store", "err", err)
		os.Exit(1)
	}

	mux := http.NewServeMux()
	api := &API{store: store}
	api.register(mux)
	if chaosOn {
		registerChaos(mux)
	}
	if webDir != "" {
		if st, err := os.Stat(webDir); err == nil && st.IsDir() {
			mux.Handle("GET /", withAPICookie(http.FileServer(http.Dir(webDir))))
		} else {
			logger.Warn("WEB_DIR not found, serving the API only", "web_dir", webDir)
			webDir = ""
		}
	}

	srv := &http.Server{
		Handler: accessLog(mux),
		// Timeouts stop slow or stuck clients from holding connections (and file descriptors) forever.
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      60 * time.Second,
		IdleTimeout:       120 * time.Second,
		ErrorLog:          slog.NewLogLogger(logger.Handler(), slog.LevelWarn),
	}

	// Listen before logging "started", so a busy port is reported clearly.
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		logger.Error("could not listen", "addr", addr, "err", err)
		os.Exit(1)
	}
	logger.Info("started",
		"addr", ln.Addr().String(), "pid", os.Getpid(), "data_file", store.path,
		"scores_loaded", store.Count(), "web_dir", webDir, "chaos", chaosOn)

	serveErr := make(chan error, 1)
	go func() { serveErr <- srv.Serve(ln) }()

	// Signals: SIGTERM (what `systemctl stop` and `kill` send) and SIGINT (Ctrl+C)
	// trigger a graceful shutdown. SIGHUP prints a status report to the log.
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM, syscall.SIGINT, syscall.SIGHUP)

	for {
		select {
		case err := <-serveErr:
			logger.Error("server stopped unexpectedly", "err", err)
			os.Exit(1)
		case sig := <-sigs:
			if sig == syscall.SIGHUP {
				logStatus(store)
				continue
			}
			logger.Info("shutting down", "signal", sig.String())
			// Stop accepting new connections, and give requests in flight up to 10s to finish.
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			if err := srv.Shutdown(ctx); err != nil && !errors.Is(err, http.ErrServerClosed) {
				logger.Warn("requests still running at shutdown deadline", "err", err)
			}
			cancel()
			store.Close()
			logger.Info("stopped", "uptime_s", int(time.Since(started).Seconds()))
			return
		}
	}
}

// withAPICookie tells the frontend that this backend is here, so it shows the
// leaderboard. (On GitHub Pages there is no cookie and no leaderboard.)
func withAPICookie(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, &http.Cookie{Name: "geoquiz_api", Value: "1", Path: "/", SameSite: http.SameSiteLaxMode})
		next.ServeHTTP(w, r)
	})
}

// logStatus is what `kill -HUP <pid>` prints: a quick look inside the process.
func logStatus(store *Store) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	logger.Info("status",
		"pid", os.Getpid(),
		"uptime_s", int(time.Since(started).Seconds()),
		"scores", store.Count(),
		"goroutines", runtime.NumGoroutine(),
		"open_fds", openFDs(),
		"heap_mb", m.HeapAlloc>>20,
		"go_sys_mb", m.Sys>>20,
	)
}

// openFDs counts this process's open file descriptors (Linux only; -1 elsewhere).
func openFDs() int {
	entries, err := os.ReadDir("/proc/self/fd")
	if err != nil {
		return -1
	}
	return len(entries)
}

type statusRecorder struct {
	http.ResponseWriter
	status int
	bytes  int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func (r *statusRecorder) Write(b []byte) (int, error) {
	if r.status == 0 {
		r.status = http.StatusOK
	}
	n, err := r.ResponseWriter.Write(b)
	r.bytes += n
	return n, err
}

// accessLog writes one log line per request: the raw material for debugging,
// and later for metrics and SLOs.
func accessLog(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w}
		next.ServeHTTP(rec, r)
		if rec.status == 0 {
			rec.status = http.StatusOK
		}
		level := slog.LevelInfo
		if rec.status >= 500 {
			level = slog.LevelError
		}
		logger.Log(r.Context(), level, "request",
			"method", r.Method,
			"path", r.URL.Path,
			"status", rec.status,
			"bytes", rec.bytes,
			"duration_ms", float64(time.Since(start).Microseconds())/1000,
			"remote", r.RemoteAddr,
		)
	})
}
