// @ts-check
const { test, expect } = require('@playwright/test');

/** Fail the test on any uncaught error or console error. */
function trackErrors(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  return errors;
}

async function loadCountries(request) {
  const res = await request.get('data/countries.json');
  expect(res.ok()).toBeTruthy();
  return res.json();
}

async function startQuiz(page) {
  await page.goto('./');
  await expect(page.locator('#start-btn')).toBeEnabled();
  await page.locator('#start-btn').click();
  await expect(page.locator('#screen-quiz')).toBeVisible();
}

test('home screen loads with all countries', async ({ page, request }) => {
  const errors = trackErrors(page);
  const countries = await loadCountries(request);
  await page.goto('./');
  await expect(page.locator('#start-btn')).toHaveText('Start quiz');
  await expect(page.getByText(`All ${countries.length}`)).toBeVisible();
  expect(errors).toEqual([]);
});

test('playing a quiz: right answer, wrong answer, finish', async ({ page, request }) => {
  const errors = trackErrors(page);
  const [first, second] = await loadCountries(request); // default order: increasing difficulty
  await startQuiz(page);

  await expect(page.locator('#score')).toHaveText('0 / 10');
  await page.locator('#answer').fill(first.name.toLowerCase());
  await page.locator('#answer').press('Enter');
  await expect(page.locator('#feedback')).toContainText(first.name);
  await expect(page.locator('#score')).toHaveText('1 / 10');

  await expect(page.locator('#question-count')).toHaveText('1 of 10 answered');
  await page.locator('#answer').fill('definitely not a country');
  await page.locator('#answer').press('Enter');
  await expect(page.locator('#feedback')).toHaveText(`It was ${second.name}`);

  await expect(page.locator('#question-count')).toHaveText('2 of 10 answered');
  await page.getByRole('button', { name: 'Finish & see score' }).click();
  await expect(page.locator('#final-score')).toHaveText('1 / 10');
  await expect(page.locator('#final-time')).toHaveText(/⏱ \d+:\d\d/);
  // The wrong answer first, then the 8 countries not answered yet
  await expect(page.locator('#missed li')).toHaveCount(9);
  await expect(page.locator('#missed li').first()).toHaveText(second.name);
  await expect(page.locator('#missed li').nth(1)).toContainText('not answered');
  expect(errors).toEqual([]);
});

test('skip for now brings the country back at the end', async ({ page, request }) => {
  const [first, second] = await loadCountries(request);
  await page.goto('./');
  await page.locator('input[name="count"][value="custom"]').check();
  await page.locator('#custom-count').fill('2');
  await page.locator('#start-btn').click();
  await expect(page.locator('#shape')).toHaveAttribute('src', first.image);

  await page.getByRole('button', { name: 'Skip for now' }).click();
  await expect(page.locator('#shape')).toHaveAttribute('src', second.image);
  await expect(page.locator('#question-count')).toHaveText('0 of 2 answered');
  await page.locator('#answer').fill(second.name);
  await page.locator('#answer').press('Enter');

  // The skipped country comes back, and there is nothing left to skip to
  await expect(page.locator('#shape')).toHaveAttribute('src', first.image);
  await expect(page.locator('#feedback')).toHaveText('You skipped this one earlier');
  await expect(page.getByRole('button', { name: 'Skip for now' })).toBeDisabled();
  await page.locator('#answer').fill(first.name);
  await page.locator('#answer').press('Enter');
  await expect(page.locator('#final-score')).toHaveText('2 / 2');
  await expect(page.locator('#missed-wrap')).toBeHidden();
});

test('the timer counts up while playing', async ({ page }) => {
  await page.clock.install();
  await startQuiz(page);
  await expect(page.locator('#clock')).toHaveText('0:00');
  await page.clock.runFor(65_000);
  await expect(page.locator('#clock')).toHaveText('1:05');
  await page.getByRole('button', { name: 'Finish & see score' }).click();
  await expect(page.locator('#final-time')).toHaveText('⏱ 1:05');
});

test('the quiz screen fits without scrolling', async ({ page }) => {
  await startQuiz(page);
  await expect(page.locator('#shape')).toHaveJSProperty('complete', true);
  const fit = await page.evaluate(() => ({
    scroll: document.documentElement.scrollHeight,
    viewport: window.innerHeight,
    skipBottom: document.getElementById('skip-btn').getBoundingClientRect().bottom,
    shapeHeight: document.getElementById('shape-wrap').getBoundingClientRect().height,
  }));
  expect(fit.scroll).toBeLessThanOrEqual(fit.viewport);
  expect(fit.skipBottom).toBeLessThanOrEqual(fit.viewport);
  expect(fit.shapeHeight).toBeGreaterThan(140);
});

test('every country has a valid SVG shape', async ({ request }) => {
  const countries = await loadCountries(request);
  expect(countries.length).toBeGreaterThan(150);
  const ids = new Set();
  for (const c of countries) {
    expect(ids.has(c.id), `duplicate id ${c.id}`).toBeFalsy();
    ids.add(c.id);
    expect(c.aliases.length, `${c.name} has no answers`).toBeGreaterThan(0);
    const res = await request.get(c.image);
    expect(res.ok(), `${c.image} missing`).toBeTruthy();
    const body = await res.text();
    expect(body.startsWith('<svg'), `${c.image} is not an SVG`).toBeTruthy();
  }
});

test('manifest and icons are valid for installing the app', async ({ request }) => {
  const res = await request.get('manifest.webmanifest');
  expect(res.ok()).toBeTruthy();
  const manifest = await res.json();
  expect(manifest.name).toBeTruthy();
  expect(manifest.icons.length).toBeGreaterThan(0);
  for (const icon of manifest.icons) {
    expect((await request.get(icon.src)).ok(), `${icon.src} missing`).toBeTruthy();
  }
});

test('works offline after the first visit', async ({ page, context, browserName }) => {
  test.skip(browserName !== 'chromium', 'service worker check uses Chromium');
  await page.goto('./');
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload(); // let the service worker control the page
  await context.setOffline(true);
  await page.reload();
  await expect(page.locator('#start-btn')).toBeEnabled();
  await page.locator('#start-btn').click();
  await expect(page.locator('#screen-quiz')).toBeVisible();
});
