(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const SETTINGS_KEY = 'geoquiz-settings';

  const state = {
    countries: [],
    ownerOf: new Map(),
    questions: [],
    score: 0,
    missed: [],
    settings: { order: 'difficulty', count: '10', custom: '', showAnswers: true, sound: true },
    queue: [],
    skipped: new Set(),
    busy: false,
    pending: null, // pause after an answer before the next country
    clock: null,
    startedAt: 0,
    endedAt: 0,
  };

  // ---------- Sound ----------
  const sounds = {
    correct: new Audio('sound/correct.wav'),
    wrong: new Audio('sound/wrong.mp3'),
  };
  function play(name) {
    if (!state.settings.sound) return;
    const s = sounds[name];
    s.currentTime = 0;
    s.play().catch(() => {}); // autoplay restrictions are fine to ignore
  }

  // ---------- Screens ----------
  function show(screen) {
    document.querySelectorAll('.screen').forEach((el) => el.classList.toggle('active', el.id === `screen-${screen}`));
    document.body.dataset.screen = screen;
    window.scrollTo(0, 0);
  }

  // ---------- Settings ----------
  function loadSettings() {
    try {
      Object.assign(state.settings, JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {});
    } catch (_) { /* storage unavailable */ }
    const form = $('settings');
    form.order.value = state.settings.order;
    form.count.value = state.settings.count;
    form.showAnswers.checked = state.settings.showAnswers;
    form.sound.checked = state.settings.sound;
    $('custom-count').value = state.settings.custom;
    $('custom-count').hidden = state.settings.count !== 'custom';
  }

  function readSettings() {
    const form = $('settings');
    state.settings = {
      order: form.order.value,
      count: form.count.value,
      custom: $('custom-count').value,
      showAnswers: form.showAnswers.checked,
      sound: form.sound.checked,
    };
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings)); } catch (_) { /* ignore */ }
  }

  function questionCount() {
    const total = state.countries.length;
    const { count, custom } = state.settings;
    if (count === 'all') return total;
    const n = parseInt(count === 'custom' ? custom : count, 10);
    return Number.isFinite(n) && n > 0 ? Math.min(n, total) : 10;
  }

  // ---------- Quiz flow ----------
  function shuffle(list) {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // ---------- Timer ----------
  function formatTime(ms) {
    const total = Math.floor(ms / 1000);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const sec = String(total % 60).padStart(2, '0');
    return h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
  }

  function elapsed() {
    return (state.endedAt || Date.now()) - state.startedAt;
  }

  function tick() {
    $('clock').textContent = formatTime(elapsed());
  }

  function startClock() {
    stopClock();
    state.startedAt = Date.now();
    state.endedAt = 0;
    tick();
    state.clock = setInterval(tick, 1000);
  }

  function stopClock() {
    clearInterval(state.clock);
    state.clock = null;
    if (state.startedAt && !state.endedAt) state.endedAt = Date.now();
  }

  // ---------- Quiz flow ----------
  // state.queue holds the countries still to answer; the first one is on screen.
  // "Skip for now" moves it to the back of the queue so it comes back later.

  function cancelPending() {
    clearTimeout(state.pending);
    state.pending = null;
  }

  function startQuiz() {
    cancelPending();
    const n = questionCount();
    state.questions = state.settings.order === 'random'
      ? shuffle(state.countries).slice(0, n)
      : state.countries.slice(0, n);
    state.queue = state.questions.slice();
    state.skipped = new Set();
    state.score = 0;
    state.missed = [];
    show('quiz');
    startClock();
    showQuestion();
  }

  function preload(q) {
    if (q) new Image().src = q.image;
  }

  function showQuestion() {
    const q = state.queue[0];
    if (!q) return finishQuiz();
    state.busy = false;
    const total = state.questions.length;
    const answered = total - state.queue.length;
    $('shape').src = q.image;
    $('shape-wrap').className = 'shape';
    $('feedback').className = 'feedback';
    $('feedback').textContent = state.skipped.has(q.id) ? 'You skipped this one earlier' : '';
    $('answer').value = '';
    $('answer').disabled = false;
    $('submit-btn').disabled = false;
    $('skip-btn').disabled = state.queue.length < 2; // nothing to come back to
    $('question-count').textContent = `${answered} of ${total} answered`;
    $('progress').style.width = `${(answered / total) * 100}%`;
    updateScore();
    $('answer').focus();
    preload(state.queue[1]);
  }

  function updateScore() {
    $('score').textContent = `${state.score} / ${state.questions.length}`;
  }

  function skipQuestion() {
    if (state.busy || state.queue.length < 2) return;
    const q = state.queue.shift();
    state.queue.push(q);
    state.skipped.add(q.id);
    showQuestion();
  }

  function submitAnswer() {
    if (state.busy) return;
    const q = state.queue[0];
    const answer = $('answer').value;
    if (!answer.trim()) return $('answer').focus();

    state.busy = true;
    $('answer').disabled = true;
    $('submit-btn').disabled = true;
    $('skip-btn').disabled = true;

    let delay = 700;
    if (GeoMatch.isCorrect(answer, q, state.ownerOf)) {
      state.score++;
      play('correct');
      $('feedback').textContent = `✓ ${q.name}`;
      $('feedback').className = 'feedback good';
      $('shape-wrap').className = 'shape good';
    } else {
      state.missed.push(q);
      play('wrong');
      $('shape-wrap').className = 'shape bad';
      $('feedback').className = 'feedback bad';
      if (state.settings.showAnswers) {
        $('feedback').textContent = `It was ${q.name}`;
        delay = 1800;
      } else {
        $('feedback').textContent = '✗ Not quite';
      }
    }
    updateScore();
    state.pending = setTimeout(() => {
      state.pending = null;
      state.queue.shift();
      showQuestion();
    }, delay);
  }

  function reviewItem(country, note) {
    const li = document.createElement('li');
    const img = document.createElement('img');
    img.src = country.image;
    img.alt = '';
    img.loading = 'lazy';
    const name = document.createElement('span');
    name.textContent = country.name;
    li.append(img, name);
    if (note) {
      const small = document.createElement('span');
      small.className = 'note';
      small.textContent = note;
      li.append(small);
    }
    return li;
  }

  function finishQuiz() {
    // Finishing during the feedback pause still counts the answer just given.
    if (state.pending) {
      cancelPending();
      state.queue.shift();
    }
    stopClock();
    const total = state.questions.length;
    const unanswered = state.queue.slice();
    const answered = total - unanswered.length;
    const time = formatTime(elapsed());
    $('final-score').textContent = `${state.score} / ${total}`;
    $('final-time').textContent = `⏱ ${time}`;
    const pct = total ? state.score / total : 0;
    $('final-message').textContent =
      answered < total ? `You answered ${answered} of ${total} before finishing.` :
      pct === 1 ? 'Perfect! You know your shapes.' :
      pct >= 0.7 ? 'Great job!' :
      pct >= 0.4 ? 'Not bad, keep practising!' : 'Every expert started somewhere. Try again!';

    $('missed').replaceChildren(
      ...state.missed.map((c) => reviewItem(c)),
      ...unanswered.map((c) => reviewItem(c, 'not answered'))
    );
    $('missed-wrap').hidden = state.missed.length + unanswered.length === 0;
    show('results');
    $('again-btn').focus();
  }

  // ---------- Wiring ----------
  function bind() {
    const form = $('settings');
    form.addEventListener('change', () => {
      $('custom-count').hidden = form.count.value !== 'custom';
      if (form.count.value === 'custom') $('custom-count').focus();
    });
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      readSettings();
      startQuiz();
    });
    $('answer-form').addEventListener('submit', (e) => {
      e.preventDefault();
      submitAnswer();
    });
    $('skip-btn').addEventListener('click', skipQuestion);
    $('quit-btn').addEventListener('click', finishQuiz);
    $('again-btn').addEventListener('click', startQuiz);
    $('home-btn').addEventListener('click', () => show('home'));
    // Keep the clock honest when the phone wakes up from the background.
    document.addEventListener('visibilitychange', () => { if (state.clock) tick(); });
  }

  async function init() {
    loadSettings();
    bind();
    try {
      const res = await fetch('data/countries.json');
      state.countries = await res.json();
      state.ownerOf = GeoMatch.buildOwnerIndex(state.countries);
      $('start-btn').disabled = false;
      $('start-btn').textContent = 'Start quiz';
      $('custom-count').max = state.countries.length;
      document.querySelector('input[name="count"][value="all"] + span').textContent = `All ${state.countries.length}`;
    } catch (err) {
      $('start-btn').textContent = 'Could not load countries';
      console.error(err);
    }
    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }

  init();
})();
