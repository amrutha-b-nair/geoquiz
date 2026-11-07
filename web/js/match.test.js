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
