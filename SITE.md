# The Electrode Budget — GitHub Pages site

The benchmark now has a static, dependency-free website under `docs/`. It is
designed for people outside EEG: each task gets a plain-language explanation,
a real signal illustration, and an interactive montage explorer.

## Preview locally

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
# open http://localhost:8000
```

The page needs an HTTP server (it fetches JSON). Opening `docs/index.html`
directly will not work because browsers block `fetch()` on `file://`.

Useful query parameters while editing:

```
?static=1          reveal all sections (good for screenshots/printing)
?theme=light       force the light theme
?theme=dark        force the dark theme
?task=ssvep_8ch    open a specific task in the explorer
&view=delta        open the delta-vs-reference view
&metric=itr        show SSVEP bits/min instead of accuracy
```

## Publish it

The repository root is not a git checkout yet. From the project root:

```powershell
git init
git add .
git commit -m "Add EEG wearable benchmark site"

# create an empty repository on GitHub first, then:
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Then on GitHub:

1. **Settings → Pages**
2. **Build and deployment → Source: GitHub Actions**
3. Push again (or run the **Deploy GitHub Pages** workflow manually).

The workflow in `.github/workflows/pages.yml` uploads `docs/` as the site.

- If the repo is named `<you>.github.io`, the site is
  `https://<you>.github.io/`.
- Otherwise it is `https://<you>.github.io/<repo>/`.
- All links in the site are relative, so it works from either path.

`.nojekyll` is present so GitHub serves the JSON and SVG files unchanged.

## What is in `docs/`

```
docs/
├── index.html              page structure and editorial copy
├── assets/
│   ├── styles.css          light/dark themes + responsive layout
│   ├── app.js              SVG charts, head maps, explorer
│   └── favicon.svg
├── data/
│   ├── benchmark.json      every result, generated from results/benchmark/
│   └── signals.json        real EEG illustrations, generated from data/
└── .nojekyll
```

Nothing in the HTML is hand-transcribed from the benchmark. The numbers come
from `docs/data/benchmark.json`, which is written by:

```powershell
.\.venv\Scripts\python.exe scripts\build_site.py
```

That script reads `results/benchmark/*.csv`, `results/perm_control_*.csv` and
`results/signal_quality_bnci.csv`, adds the task metadata and electrode
positions, and writes the JSON bundle. The raw datasets are not needed.

The real-data illustrations (one trial, one ERP average, one spectrum, one
hypnogram) are generated once with:

```powershell
.\.venv\Scripts\python.exe scripts\build_site_signals.py
```

They are then committed, so a fresh clone can build the page without the
multi-gigabyte datasets. Re-run the signal script only if you change the
illustration selection.

## Updating the site after a benchmark run

```powershell
# 1. regenerate the benchmark tables (as usual)
.\.venv\Scripts\python.exe scripts\report.py

# 2. regenerate the site's data bundle
.\.venv\Scripts\python.exe scripts\build_site.py

# 3. commit docs/data/benchmark.json (and any legitimate result CSVs)
git add docs/data/benchmark.json results/benchmark
git commit -m "Update benchmark site data"
git push
```

If a result changes meaning rather than just value (new track, new decoder,
new caveat), update the matching entry in `TASKS` inside
`scripts/build_site.py` and the prose in `docs/index.html`.

## Editing notes

- **Colours** live as CSS variables at the top of `docs/assets/styles.css`;
  the SVG charts use the same variables so light/dark mode needs no redraw.
- **Electrode maps** are drawn from `docs/data/benchmark.json` → `positions`.
  Scalp positions come from MNE's 10-5 montage; ear labels are schematic.
- **Chance is task-aware.** The site does not rely on the older leaderboard's
  per-row chance column, which cannot infer a metric for the pre-`metric`
  CSVs. It uses the task definition: ROC-AUC 0.5, accuracy 1/n, κ 0.
- **No chart library.** Everything is hand-drawn SVG, so the page has no
  JavaScript dependency beyond `app.js` and loads quickly.

## Suggested repository metadata

- Description: *How much EEG accuracy survives when a lab cap becomes a
  wearable? A montage benchmark across six public datasets.*
- Topics: `eeg`, `brain-computer-interface`, `wearable`, `benchmark`,
  `neuroscience`, `moabb`
- Social preview: use a screenshot of the hero section (`docs/_preview` files
  are not committed; take one with `?static=1&theme=light`).
