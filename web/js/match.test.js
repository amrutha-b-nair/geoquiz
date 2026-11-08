// Run with: node --test web/js/match.test.js
const test = require('node:test');
const assert = require('node:assert');
const { isCorrect, buildOwnerIndex } = require('./match.js');

const countries = [
  { id: 'india', aliases: ['India', 'Republic of India', 'Bharat'] },
  { id: 'australia', aliases: ['Australia'] },
  { id: 'austria', aliases: ['Austria'] },
  { id: 'united-states', aliases: ['United States', 'USA', 'US', 'America'] },
  { id: 'united-kingdom', aliases: ['United Kingdom', 'UK'] },
  { id: 'sao-tome-and-principe', aliases: ['São Tomé and Príncipe'] },
  { id: 'congo', aliases: ['Congo', 'Republic of the Congo'] },
  { id: 'democratic-republic-of-congo', aliases: ['Democratic Republic of Congo', 'DRC', 'Congo'] },
  { id: 'niger', aliases: ['Niger'] },
  { id: 'nigeria', aliases: ['Nigeria'] },
];
const owners = buildOwnerIndex(countries);
const byId = Object.fromEntries(countries.map((c) => [c.id, c]));
const check = (answer, id) => isCorrect(answer, byId[id], owners);

test('exact and case-insensitive answers', () => {
  assert.ok(check('India', 'india'));
  assert.ok(check('  BHARAT ', 'india'));
  assert.ok(check('usa', 'united-states'));
});

test('forgives small typos', () => {
  assert.ok(check('indai', 'india'));
  assert.ok(check('Untied States', 'united-states'));
  assert.ok(check('sao tome and principe', 'sao-tome-and-principe'));
});

test('another real country is never a typo', () => {
  assert.ok(!check('Austria', 'australia'));
  assert.ok(!check('Australia', 'austria'));
  assert.ok(!check('Niger', 'nigeria'));
  assert.ok(!check('UK', 'united-states'));
});

test('aliases shared by two countries count for both', () => {
  assert.ok(check('Congo', 'congo'));
  assert.ok(check('Congo', 'democratic-republic-of-congo'));
});

test('empty answers are wrong', () => {
  assert.ok(!check('', 'india'));
  assert.ok(!check('   ', 'india'));
});

test('dots, apostrophes and "St" abbreviations are ignored', () => {
  const uk = { id: 'uk', aliases: ['U.K.'] };
  assert.ok(isCorrect('UK', uk));
  assert.ok(isCorrect('u.k.', uk));
  assert.ok(isCorrect('St Lucia', { id: 'lc', aliases: ['Saint Lucia'] }));
  assert.ok(isCorrect('St. Lucia', { id: 'lc', aliases: ['Saint Lucia'] }));
  assert.ok(isCorrect("cote d'ivoire", { id: 'ci', aliases: ["Côte d'Ivoire"] }));
});

test('common names are accepted with the real country data', () => {
  const data = require('../data/countries.json');
  const index = buildOwnerIndex(data);
  const country = (id) => data.find((c) => c.id === id);
  const cases = {
    'united-kingdom': ['UK', 'U.K.', 'uk', 'Britain', 'Great Britain', 'United Kingdom'],
    'united-states': ['US', 'USA', 'U.S.A.', 'America'],
    'united-arab-emirates': ['UAE', 'U.A.E.'],
    'democratic-republic-of-congo': ['DRC', 'DR Congo'],
    'people-s-republic-of-china': ['China', 'PRC'],
    'romania': ['Rumania', 'Roumania'],
    'saint-kitts-and-nevis': ['St Kitts and Nevis', 'Saint Christopher'],
    'saint-lucia': ['St Lucia'],
    'cote-d-ivoire': ['Ivory Coast', "Cote d'Ivoire"],
    'czech-republic': ['Czechia'],
    'turkey': ['Türkiye'],
    'the-gambia': ['Gambia'],
    'myanmar': ['Burma'],
  };
  for (const [id, answers] of Object.entries(cases)) {
    assert.ok(country(id), `missing country ${id}`);
    for (const answer of answers) {
      assert.ok(isCorrect(answer, country(id), index), `"${answer}" should be accepted for ${id}`);
    }
  }
  assert.ok(!isCorrect('UK', country('united-states'), index));
  assert.ok(!isCorrect('Niger', country('nigeria'), index));
});
