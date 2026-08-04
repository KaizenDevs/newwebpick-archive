# NewWebPick Archive

44 issues of NewWebPick — a Flash-based digital design magazine (2004–2010).

Original files were PowerPC Flash projectors and `.app` bundles. Extracted to `.swf` for playback via [Ruffle](https://ruffle.rs) (web build).

## Layout

- `site/` — served output: `index.html`, `covers/*.png`, `swf/*.swf`
- `scripts/` — source tooling: extraction, cover generation, screenshot harness

## View the archive

```bash
yarn dev
open http://localhost:8642/index.html
```

Sidebar lists all issues with cover thumbnails; click one to play it in-browser.

## Re-extract from originals

Originals must be at `/Users/german-hernandez/Documents/NewWebPick/`.

```bash
python3 scripts/extract.py
```

## Regenerate covers

```bash
python3 scripts/make_covers.py
```

## Deploy

Pushes to `main` that touch `site/**` auto-deploy to GitHub Pages via `.github/workflows/deploy.yml` (checks out with Git LFS, since `.swf` files are LFS-tracked, then publishes `site/`). Repo Pages source must be set to "GitHub Actions" in repo settings.
