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
  js/match.test.js      tests: node --test web/js/match.test.js
  data/countries.json   countries, alternative names, image paths (difficulty order)
  img/countries/*.webp  country silhouettes
  sound/                correct / wrong sounds
  sw.js                 service worker for offline play
  manifest.webmanifest  PWA manifest (install to home screen)
tools/build_web_data.py regenerates web/data and web/img from python/
python/                 the original Tkinter desktop app and data-prep scripts
.github/workflows/pages.yml  deploys web/ to GitHub Pages
```

## Run locally

Any static file server works. For example:

```bash
python3 -m http.server -d web 8000
```

Then open http://localhost:8000.

## Publish on GitHub Pages

1. Merge into `main`.
2. In the repo, go to **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
3. The *Deploy to GitHub Pages* workflow publishes `web/` on every push to `main` that changes it. You can also run it by hand from the **Actions** tab.

When you change files in `web/`, bump `VERSION` in `web/sw.js` so returning players get the update and not their cached copy.

## Turning it into a mobile app later

`web/` is a self-contained static site, so any WebView wrapper can use it directly.

- **Capacitor** (recommended, Android + iOS):
  ```bash
  npm init -y
  ```
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

The shapes and names come from the original Python project in `python/`. After changing `python/geoquiz/csv/selected_names.csv` or the images, regenerate the web data (requires Pillow):

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
