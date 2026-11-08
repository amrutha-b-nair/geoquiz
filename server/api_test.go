package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func newTestServer(t *testing.T, dir string) (*httptest.Server, *Store) {
	t.Helper()
	store, err := OpenStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	(&API{store: store}).register(mux)
	srv := httptest.NewServer(accessLog(mux))
	t.Cleanup(func() { srv.Close(); store.Close() })
	return srv, store
}

func post(t *testing.T, url, body string) int {
	t.Helper()
	res, err := http.Post(url+"/api/scores", "application/json", strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	res.Body.Close()
	return res.StatusCode
}

func TestScoresAndLeaderboard(t *testing.T) {
	srv, _ := newTestServer(t, t.TempDir())

	for body, want := range map[string]int{
		`{"name":"Asha","score":9,"total":10}`: 201,
		`{"name":"Ben","score":20,"total":25}`: 201,
		`{"name":"Cy","score":10,"total":10}`:  201,
		`{"name":"","score":1,"total":10}`:     400,
		`{"name":"Dee","score":11,"total":10}`: 400,
		`{"name":"Eve","score":1,"total":500}`: 400,
		`{"name":"Fay","score":-1,"total":10}`: 400,
		`not json`:                             400,
	} {
		if got := post(t, srv.URL, body); got != want {
			t.Errorf("POST %s: got %d, want %d", body, got, want)
		}
	}

	res, err := http.Get(srv.URL + "/api/leaderboard")
	if err != nil {
		t.Fatal(err)
	}
	defer res.Body.Close()
	var out struct{ Scores []Score }
	if err := json.NewDecoder(res.Body).Decode(&out); err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, s := range out.Scores {
		names = append(names, s.Name)
	}
	if got := strings.Join(names, ","); got != "Cy,Asha,Ben" {
		t.Errorf("leaderboard order = %s, want Cy,Asha,Ben", got)
	}
}

func TestScoresSurviveRestart(t *testing.T) {
	dir := t.TempDir()
	srv, store := newTestServer(t, dir)
	post(t, srv.URL, `{"name":"Asha","score":5,"total":10}`)
	srv.Close()
	store.Close()

	again, err := OpenStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer again.Close()
	if again.Count() != 1 {
		t.Fatalf("after restart: %d scores, want 1", again.Count())
	}
}

func TestHealthz(t *testing.T) {
	srv, _ := newTestServer(t, t.TempDir())
	res, err := http.Get(srv.URL + "/api/healthz")
	if err != nil {
		t.Fatal(err)
	}
	res.Body.Close()
	if res.StatusCode != 200 {
		t.Fatalf("healthz = %d, want 200", res.StatusCode)
	}
}
