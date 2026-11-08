# GeoQuiz: Name the Country From Its Shape

A geography quiz. You see a country's silhouette and type its name. Small spelling mistakes are forgiven. It covers 197 countries.

GeoQuiz is a static web app written in plain HTML, CSS and JavaScript, with no build step and no dependencies. It runs on **GitHub Pages**, can be **installed as an app** (it's a PWA), works **offline**, and can later be wrapped as an Android/iOS app.

## Play

After deployment it's live at `https://<your-user>.github.io/geoquiz/`.

1. Choose the order: **increasing difficulty** or **random**.
2. Choose how many countries: 10, 25, all, or a custom number.
3. Choose whether to **show the correct answer** after a mistake, and whether to play **sound**.
4. Type the country name and press Enter. You can also skip, or finish early.
5. At the end you'll see your score and the countries you missed.

## Project layout

```
web/                    ← the app (this folder is what gets published)
  index.html
  css/style.css
  js/app.js             quiz logic and UI
  js/match.js           answer matching (exact, alternative names, typo tolerance)
  js/match.test.js      unit tests (npm run test:unit)
  data/countries.json   countries, alternative names, image paths (difficulty order)
  img/countries/*.svg   country silhouettes (drawn from GeoJSON)
  sound/                correct / wrong sounds
  sw.js                 service worker for offline play
  manifest.webmanifest  PWA manifest (install to home screen)
server/                 geoquiz-scores: optional Go leaderboard API (see server/README.md)
docs/sre/               a hands-on SRE course built around operating server/
tools/build_web_data.py regenerates web/data and web/img from python/
tests/e2e/              browser tests (Playwright)
python/                 the original Tkinter desktop app and data-prep scripts
.github/                CI, Pages deploy and Dependabot (see below)
```

## Run locally

Any static file server works. For example:

```bash
python3 -m http.server -d web 8000
```

Then open http://localhost:8000.

To play with the **leaderboard**, run the Go backend instead. It serves the game and the API together:

```bash
cd server && go run .
```

Then open http://localhost:8080. See [server/README.md](server/README.md).

## Tests

```bash
npm install
```
```bash
npm test
```

`npm run test:unit` checks answer matching (no install needed). `npm run test:e2e` plays the quiz in Chromium at phone and desktop sizes. The first time, install the browser with `npx playwright install chromium`.

## GitHub Actions

| Workflow | When it runs | What it does |
|---|---|---|
| **CI** (`ci.yml`) | Every pull request, and before every deploy | Runs the answer-matching tests. Rebuilds the data with `tools/build_web_data.py` and fails if `web/data` or `web/img` don't match what's committed. Plays the quiz in a real browser on phone and desktop screens (scoring, no scrolling, every country image loads, installable, works offline). |
| **Deploy to GitHub Pages** (`pages.yml`) | Push to `main` that changes the app, or by hand | Runs CI first and deploys only if it passes. Stamps the offline cache with the commit id, so players get updates automatically. |
| **Dependabot** (`dependabot.yml`) | Monthly | Opens pull requests to update the actions, Playwright and numpy. |

## Publish on GitHub Pages

1. Merge into `main`.
2. In the repo, go to **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
3. The *Deploy to GitHub Pages* workflow tests and then publishes `web/` on every push to `main` that changes it. You can also run it by hand from the **Actions** tab.

## Turning it into a mobile app later

`web/` is a self-contained static site, so any WebView wrapper can use it directly.

- **Capacitor** (recommended, Android + iOS):
  ```bash
  npm i @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
  ```
  ```bash
  npx cap init GeoQuiz com.example.geoquiz --web-dir web
  ```
  ```bash
  npx cap add android
  ```
  ```bash
  npx cap open android
  ```
- **Trusted Web Activity** (Android, Play Store): point [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) at the GitHub Pages URL.
- **Install as a PWA**: on a phone, open the site and choose *Add to Home Screen*.

The layout already handles phone notches and safe areas, dark mode and touch input, so it works well inside a WebView.

## Updating the country data

Names come from `python/geoquiz/csv/selected_names.csv` and shapes from the GeoJSON files in `python/geojson files/`. The build script draws each country as an SVG. Parts far from the mainland, such as Alaska, Hawaii or French Guiana, go in dashed boxes beside it. They're at the same scale, so their sizes are accurate, but the distance between them isn't shown. After changing the data, regenerate it and commit the result (CI checks this):

```bash
pip install -r tools/requirements.txt
```

```bash
python3 tools/build_web_data.py
```

## Original desktop version

The original Tkinter app is still in `python/` and is published on PyPI as `geoquiz`:

```bash
pipx install geoquiz
```

## Acknowledgments

- Country shapes were made from GeoJSON files from [geojson-maps.ash.ms](https://geojson-maps.ash.ms/), [geoBoundaries](https://www.geoboundaries.org/index.html) and [Princeton/Stanford maps](https://maps.princeton.edu/catalog/stanford-sn252ts8433).
- Sounds: [Mudkip2016](https://freesound.org/people/Mudkip2016/sounds/423930/) and [Gronkjaer](https://freesound.org/people/Gronkjaer/sounds/554053/) on freesound.org.
