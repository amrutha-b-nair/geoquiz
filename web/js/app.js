(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const SETTINGS_KEY = 'geoquiz-settings';

  const state = {
    countries: [],
    ownerOf: new Map(),
    questions: [],
    index: 0,
    score: 0,
    missed: [],
    settings: { order: 'difficulty', count: '10', custom: '', showAnswers: true, sound: true },
    busy: false,
    timer: null,
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

  function stopTimer() {
    clearTimeout(state.timer);
    state.timer = null;
  }

  function startQuiz() {
    stopTimer();
    const n = questionCount();
    state.questions = state.settings.order === 'random'
      ? shuffle(state.countries).slice(0, n)
      : state.countries.slice(0, n);
    state.index = 0;
    state.score = 0;
    state.missed = [];
    show('quiz');
    showQuestion();
  }

  function preload(i) {
    const q = state.questions[i];
    if (q) new Image().src = q.image;
  }

  function showQuestion() {
    const q = state.questions[state.index];
    if (!q) return finishQuiz();
    state.busy = false;
    $('shape').src = q.image;
    $('feedback').textContent = '';
    $('feedback').className = 'feedback';
    $('shape-wrap').className = 'shape';
    $('answer').value = '';
    $('answer').disabled = false;
    $('submit-btn').disabled = false;
    $('skip-btn').disabled = false;
    $('question-count').textContent = `Country ${state.index + 1} of ${state.questions.length}`;
    $('progress').style.width = `${(state.index / state.questions.length) * 100}%`;
    updateScore();
    $('answer').focus();
    preload(state.index + 1);
  }

  function updateScore() {
    $('score').textContent = `${state.score} / ${state.questions.length}`;
  }

  function submitAnswer(skipped) {
    if (state.busy) return;
    const q = state.questions[state.index];
    const answer = $('answer').value;
    if (!skipped && !answer.trim()) return $('answer').focus();

    state.busy = true;
    $('answer').disabled = true;
    $('submit-btn').disabled = true;
    $('skip-btn').disabled = true;

    const right = !skipped && GeoMatch.isCorrect(answer, q, state.ownerOf);
    let delay = 700;
    if (right) {
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
        $('feedback').textContent = skipped ? 'Skipped' : '✗ Not quite';
      }
    }
    updateScore();
    state.timer = setTimeout(() => {
      state.timer = null;
      state.index++;
      showQuestion();
    }, delay);
  }

  function finishQuiz() {
    // Finishing during the feedback pause still counts the answer just given.
    if (state.timer) {
      stopTimer();
      state.index++;
    }
    const total = state.questions.length;
    const answered = Math.min(state.index, total);
    $('final-score').textContent = `${state.score} / ${total}`;
    const pct = total ? state.score / total : 0;
    $('final-message').textContent =
      answered < total ? `You answered ${answered} of ${total} before finishing.` :
      pct === 1 ? 'Perfect! You know your shapes.' :
      pct >= 0.7 ? 'Great job!' :
      pct >= 0.4 ? 'Not bad, keep practising!' : 'Every expert started somewhere. Try again!';

    const list = $('missed');
    list.replaceChildren(...state.missed.map((c) => {
      const li = document.createElement('li');
      const img = document.createElement('img');
      img.src = c.image;
      img.alt = '';
      img.loading = 'lazy';
      const span = document.createElement('span');
      span.textContent = c.name;
      li.append(img, span);
      return li;
    }));
    $('missed-wrap').hidden = state.missed.length === 0;
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
      submitAnswer(false);
    });
    $('skip-btn').addEventListener('click', () => submitAnswer(true));
    $('quit-btn').addEventListener('click', finishQuiz);
    $('again-btn').addEventListener('click', startQuiz);
    $('home-btn').addEventListener('click', () => show('home'));
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
