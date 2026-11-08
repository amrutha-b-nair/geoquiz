package main

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"
)

const (
	maxNameLen   = 24
	maxQuestions = 197 // number of countries in the quiz
)

type API struct {
	store *Store
}

func (a *API) register(mux *http.ServeMux) {
	mux.Handle("GET /api/healthz", a.withLatency(a.healthz))
	mux.Handle("GET /api/leaderboard", a.withLatency(a.leaderboard))
	mux.Handle("POST /api/scores", a.withLatency(a.addScore))
}

// withLatency applies the delay set by the "slow" chaos endpoint (zero normally).
func (a *API) withLatency(h http.HandlerFunc) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if d := extraLatency(); d > 0 {
			time.Sleep(d)
		}
		h(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}

// healthz answers "is this instance able to do its job?". It fails if the data
// file can no longer be synced. It does NOT notice a full disk: Sync has nothing
// to flush, so it succeeds while every POST /api/scores fails. That gap is on
// purpose: you find it in week 1 (lab D) and fix it later in the course.
func (a *API) healthz(w http.ResponseWriter, r *http.Request) {
	if err := a.store.Writable(); err != nil {
		logger.Error("health check failed", "err", err)
		writeJSON(w, http.StatusServiceUnavailable, map[string]any{"status": "unhealthy", "error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"status":   "ok",
		"pid":      os.Getpid(),
		"uptime_s": int(time.Since(started).Seconds()),
	})
}

func (a *API) leaderboard(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"scores": a.store.Top(intParam(r, "limit", 10, 100))})
}

type scoreRequest struct {
	Name  string `json:"name"`
	Score int    `json:"score"`
	Total int    `json:"total"`
}

func (req *scoreRequest) validate() error {
	req.Name = strings.TrimSpace(req.Name)
	switch {
	case req.Name == "":
		return errors.New("name is required")
	case utf8.RuneCountInString(req.Name) > maxNameLen:
		return errors.New("name is too long (max 24 characters)")
	case strings.IndexFunc(req.Name, unicode.IsControl) >= 0:
		return errors.New("name contains invalid characters")
	case req.Total < 1 || req.Total > maxQuestions:
		return errors.New("total must be between 1 and 197")
	case req.Score < 0 || req.Score > req.Total:
		return errors.New("score must be between 0 and total")
	}
	return nil
}

func (a *API) addScore(w http.ResponseWriter, r *http.Request) {
	r.Body = http.MaxBytesReader(w, r.Body, 4096)
	var req scoreRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}
	if err := req.validate(); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	rec := Score{Name: req.Name, Score: req.Score, Total: req.Total, At: time.Now().UTC()}
	if err := a.store.Add(rec); err != nil {
		// The detail goes to the log for you; the client just gets a generic error.
		logger.Error("could not save score", "err", err)
		writeError(w, http.StatusInternalServerError, "could not save score")
		return
	}
	writeJSON(w, http.StatusCreated, rec)
}
