// End-to-end tests: serve web/ and play the quiz in a real browser.
// Run with: npm run test:e2e
const { defineConfig, devices } = require('@playwright/test');

const PORT = 4173;

module.exports = defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'off',
  },
  webServer: {
    command: `python3 -m http.server ${PORT} -d web`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: !process.env.CI,
    stderr: 'ignore',
  },
  projects: [
    { name: 'phone', use: { ...devices['Pixel 7'] } },
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
  ],
});
