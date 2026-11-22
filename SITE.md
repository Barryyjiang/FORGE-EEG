# The Electrode Budget — GitHub Pages site

The benchmark publishes one static page under `docs/`, with no build step on
the server and no runtime dependency beyond the files in this repository:

| URL | Page | Source |
|---|---|---|
| `/` | **Summary page** — the question, four findings, three figures, two tables | `paper/paper.html` + generated numbers |

The interactive explorer was removed once the summary page carried the same
findings: it described an earlier five-task benchmark and argued a weaker
thesis than the page. Every montage, decoder and random subset it showed is
still in `docs/data/benchmark.json`, linked from the page and the footer.

`.nojekyll` is present so GitHub serves the JSON, PNG and PDF files unchanged.

## Preview locally

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
# open http://localhost:8000
```

The page needs an HTTP server only if you are testing the JSON download links;
the page itself is static HTML and opens fine from `file://`.

Page query parameters:

```
?theme=light       force the light theme
?theme=dark        force the dark theme
&view=delta        open the delta-vs-reference view
&metric=itr        show SSVEP bits/min instead of accuracy
```

## Publish it

This directory is already a git checkout. Create an empty repository on GitHub,
then from the project root:

```powershell
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Then on GitHub:

1. **Settings → Pages**
2. **Build and deployment → Source: GitHub Actions**
3. Push again (or run the **Deploy GitHub Pages** workflow manually).

The workflow in `.github/workflows/pages.yml` uploads `docs/` as the site.

- If the repo is named `<you>.github.io`, the site is `https://<you>.github.io/`.
- Otherwise it is `https://<you>.github.io/<repo>/`.
- All links in both pages are relative, so they work from either path.

### Author, affiliation and repository URL

These are set, not placeholders:

| Field | Where |
|---|---|
| author names and affiliation | `paper/paper.html` (masthead + JSON-LD) **and** `AUTHORS` / `AFFILIATION` in `scripts/build_paper.py` |
| `REPO_URL` | `scripts/build_paper.py` (Code button + BibTeX) |
| the BibTeX entry (`bibtex()` in `scripts/build_paper.py`) | the `#cite` section |

Edit both places for the names: the template carries the visible masthead and the
generator carries the citation, and the build does not cross-check them. Re-run
`scripts/build_paper.py` after editing; nothing else needs to change.

## What is in `docs/`

```
docs/
├── index.html                    the summary page (generated)
├── assets/
│   ├── paper.css, paper.js       page styles and interactions
│   ├── favicon.svg
│   └── figures/                  paper figures: PNG (page) + PDF (vector)
├── data/
│   ├── benchmark.json            every result, generated from results/benchmark/
│   └── signals.json              real EEG illustrations, generated from data/
└── .nojekyll
```

## How the numbers stay honest

### The page is a summary, on purpose

The published page answers one question in about 1,600 words: *how much EEG
accuracy survives when a lab cap becomes a wearable, and how much of that is
about where the electrodes sit rather than how many there are.* It carries three
figures (the headline, the placement result, the paired wearable comparison) and
two tables (the nine tasks, and the confound/reproduction checks). Everything
else — per-montage tables, per-decoder comparisons, the channel-budget curves,
the full permutation-control table — lives in `results/REPORT.md` and
`docs/data/benchmark.json`, both reachable from the page.

`paper/paper_full.html` is the long-form version the summary was cut from: design,
per-task results, validity, discussion and limitations. It is **not built** and
its inline numbers are frozen at the moment it was archived. To publish it, point
`TEMPLATE` in `scripts/build_paper.py` at that file and give it its own output
path; the placeholders and tables are unchanged.

Nothing on the paper page is hand-transcribed: its tables, figures and inline
statistics are written by the generators from `results/benchmark/`. Those are
checked against the bundle whenever the prose changes, so the
generated pages and `results/REPORT.md` are authoritative if the two disagree.

```powershell
# 1. benchmark, sleep, controls, signal quality, report
.\.venv\Scripts\python.exe scripts\run_all.py

# 2. site bundle: docs/data/benchmark.json  (raw datasets not needed)
.\.venv\Scripts\python.exe scripts\build_site.py

# 3. paper figures: docs/assets/figures/*.png + *.pdf
.\.venv\Scripts\python.exe figures\build_figures.py

# 4. paper page: docs/index.html  (reads paper/paper.html + the bundle + the CSVs)
.\.venv\Scripts\python.exe scripts\build_paper.py

# 5. optional: real EEG illustrations for the data bundle
.\.venv\Scripts\python.exe scripts\build_site_signals.py
```

The paper template carries the prose and the placeholders; the generator fills
in tables, inline statistics and the BibTeX block, and fails loudly on an
unknown placeholder or a missing asset:

| Placeholder | Meaning |
|---|---|
| `{{table:NAME}}` | a generated table (`TASKS`, `DECODERS`, `RESULTS`, `WEARABLE`, `CONTROLS`) |
| `{{stat:track:field}}` | one headline number for a task, e.g. `{{stat:p300_8ch:retainedPct}}` |
| `{{cell:track:subset:field}}` | one aggregate cell, e.g. `{{cell:ssvep_8ch:distributed_k4:score}}` |
| `{{pair:name:field}}` | a paired comparison, e.g. `{{pair:inear_vs_senso:delta}}` |
| `{{meta:field}}` | a bundle metadata field (`nTasks`, `nRows`, `nExamples`, …) |
| `{{generated}}`, `{{repo}}`, `{{bibtex}}` | build date, repository URL, citation |

If a result changes meaning rather than value (new task, new decoder, new scope
note), update the matching entry in `TASKS` inside `scripts/build_site.py`, the
prose in `paper/paper.html`, and — if the comparison is new — the paired block in
`named_pairs()` inside `scripts/build_paper.py`.

## Figures

`figures/` is a small matplotlib toolkit in the style of
[figures4papers](https://github.com/ChenLiu-1996/figures4papers) (semantic
palette, spines off, frameless legends, 300 dpi PNG + vector PDF):

```
figures/
├── figure_style.py      palette, FigureStyle preset, plot helpers, export
├── paper_data.py        bundle + raw-CSV access, paired statistics
├── eeg_maps.py          top-down head maps from the bundle's electrode positions
├── plot_fig1_overview.py … plot_fig6_controls.py
└── build_figures.py     rebuild every figure (--only fig4 to build one)
```

Each script reads only `docs/data/benchmark.json` and `results/benchmark/*.csv`,
so the figures rebuild without the raw multi-gigabyte datasets.

## Editing notes

- **Theme.** The paper page is **light by default**, because a paper is read on
  white. Readers can switch with the sun/moon button in the header (remembered in
  `localStorage` under `eegbench-paper-theme`), or open it directly dark with
  `?theme=dark`. The theme is resolved by a small inline script in
  `paper/paper.html` before first paint, so there is no flash.
- **Colours** live as CSS variables at the top of `docs/assets/paper.css`. The
  matplotlib palette is in
  `figures/figure_style.py` (`PALETTE`, `COLORS`), so figures and page follow the
  same semantics: blue = reference/full cap, green = sensorimotor, red = in-ear
  and ear, neutral = random subsets.
- **Electrode maps** are drawn from `docs/data/benchmark.json` → `positions`.
  Scalp positions come from MNE's 10-5 montage; ear labels are schematic.
- **Chance is task-aware.** ROC-AUC 0.5, accuracy 1/n, Cohen's κ 0.
- **The paper page prints itself.** The "Print / PDF" button uses a print
  stylesheet; `Ctrl+P` from the paper page gives a clean PDF without extra tools.
- **No chart library and no CDN.** Everything is hand-drawn SVG or committed
  PNG/PDF, so the pages load from a plain static host.

## Suggested repository metadata

- Description: *How much EEG accuracy survives when a lab cap becomes a
  wearable? A montage benchmark across eight public datasets and nine tasks.*
- Topics: `eeg`, `brain-computer-interface`, `wearable`, `benchmark`,
  `neuroscience`, `moabb`
- Social preview: use `docs/assets/figures/fig1_overview.png` (already wired as
  the Open Graph image of the paper page).
