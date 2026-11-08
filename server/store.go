package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

// Score is one finished quiz.
type Score struct {
	Name  string    `json:"name"`
	Score int       `json:"score"`
	Total int       `json:"total"`
	At    time.Time `json:"at"`
}

// Store keeps scores in memory and appends every new score to a file on disk
// (one JSON object per line). It is deliberately simple: in week 1 that file
// is what you watch fill up a disk; in week 3 it gets replaced by Postgres.
type Store struct {
	mu     sync.RWMutex
	path   string
	file   *os.File
	scores []Score
}

// OpenStore loads existing scores from dir/scores.jsonl and opens the file for appending.
func OpenStore(dir string) (*Store, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, fmt.Errorf("create data dir: %w", err)
	}
	path := filepath.Join(dir, "scores.jsonl")
	s := &Store{path: path}

	if f, err := os.Open(path); err == nil {
		sc := bufio.NewScanner(f)
		line := 0
		for sc.Scan() {
			line++
			var rec Score
			if err := json.Unmarshal(sc.Bytes(), &rec); err != nil {
				// A half-written last line (e.g. the disk filled up mid-write) should not stop startup.
				logger.Warn("skipping unreadable line in data file", "path", path, "line", line, "err", err)
				continue
			}
			s.scores = append(s.scores, rec)
		}
		f.Close()
		if err := sc.Err(); err != nil {
			return nil, fmt.Errorf("read %s: %w", path, err)
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}

	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return nil, fmt.Errorf("open %s for append: %w", path, err)
	}
	s.file = f
	return s, nil
}

// Add writes the score to disk first and only keeps it in memory if that worked,
// so a failed write (disk full, read-only filesystem...) is reported to the caller.
func (s *Store) Add(rec Score) error {
	b, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	b = append(b, '\n')

	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := s.file.Write(b); err != nil {
		return fmt.Errorf("append score: %w", err) // err already names the file
	}
	// Sync makes the kernel flush to disk now. Without it, "disk full" could show up
	// later, or never, and a power cut could lose the score after we said "saved".
	if err := s.file.Sync(); err != nil {
		return fmt.Errorf("sync to disk: %w", err)
	}
	s.scores = append(s.scores, rec)
	return nil
}

// Top returns the best scores: highest percentage first, then more questions, then earliest.
func (s *Store) Top(n int) []Score {
	s.mu.RLock()
	out := make([]Score, len(s.scores))
	copy(out, s.scores)
	s.mu.RUnlock()

	sort.SliceStable(out, func(i, j int) bool {
		a, b := out[i], out[j]
		// Compare a.Score/a.Total with b.Score/b.Total without floating point.
		if l, r := a.Score*b.Total, b.Score*a.Total; l != r {
			return l > r
		}
		if a.Total != b.Total {
			return a.Total > b.Total
		}
		return a.At.Before(b.At)
	})
	if len(out) > n {
		out = out[:n]
	}
	return out
}

// Count is the number of stored scores.
func (s *Store) Count() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.scores)
}

// Writable checks that the data file can still be written to, for the health check.
func (s *Store) Writable() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.file.Sync()
}

func (s *Store) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.file.Close()
}
