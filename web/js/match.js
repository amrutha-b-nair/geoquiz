// Answer matching: exact alias match, or a fuzzy match that forgives small typos.
// The similarity mirrors the Python version's fuzzywuzzy `fuzz.ratio` (> 85).
(function (global) {
  'use strict';

  function normalize(text) {
    return text
      .normalize('NFKD')
      .replace(/[̀-ͯ]/g, '') // strip accents: "São Tomé" -> "Sao Tome"
      .toLowerCase()
      .replace(/&/g, ' and ')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/^the /, '')
      .trim();
  }

  // Longest common subsequence length.
  function lcs(a, b) {
    let prev = new Array(b.length + 1).fill(0);
    for (let i = 1; i <= a.length; i++) {
      const cur = [0];
      for (let j = 1; j <= b.length; j++) {
        cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
      }
      prev = cur;
    }
    return prev[b.length];
  }

  // 0-100 similarity, same formula as fuzz.ratio (indel-based).
  function ratio(a, b) {
    const total = a.length + b.length;
    return total === 0 ? 100 : Math.round((200 * lcs(a, b)) / total);
  }

  // Edit distance counting a swap of two neighbouring letters as one edit.
  function editDistance(a, b) {
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      for (let j = 1; j <= b.length; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
        }
      }
    }
    return d[a.length][b.length];
  }

  function isClose(guess, target, threshold) {
    if (target.length <= 3) return false; // short codes like "US" must be exact
    if (ratio(guess, target) > threshold) return true;
    return editDistance(guess, target) <= (target.length >= 8 ? 2 : 1);
  }

  // `ownerOf` (optional) maps every normalized alias of every country to the
  // ids of the countries using it, so typing another real country ("Austria" for "Australia")
  // is never accepted as a typo.
  function isCorrect(answer, country, ownerOf, threshold = 85) {
    const guess = normalize(answer);
    if (!guess) return false;
    const owner = ownerOf && ownerOf.get(guess);
    if (owner) return owner.has(country.id);
    return country.aliases.some((alias) => {
      const target = normalize(alias);
      return target === guess || isClose(guess, target, threshold);
    });
  }

  function buildOwnerIndex(countries) {
    const index = new Map();
    for (const c of countries) {
      for (const alias of c.aliases) {
        const key = normalize(alias);
        if (!key) continue;
        if (!index.has(key)) index.set(key, new Set());
        index.get(key).add(c.id);
      }
    }
    return index;
  }

  const api = { normalize, ratio, editDistance, isCorrect, buildOwnerIndex };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else global.GeoMatch = api;
})(this);
