# AID Lab website

Static site for the **AI & Dynamics Group (AID Lab)** at the University of Rochester,
led by Yuanzhao Zhang. Plain HTML/CSS/vanilla JS — no build step.

**Live:** https://lab.y-zhang.com

## Structure

- `*.html` — one file per page (home, research, people, publications, news, join, 404)
- `styles.css` — all styling and design tokens
- `js/` — `logo.js` (SVG mark/wordmark), `visuals.js` (research-theme SVGs),
  `flow-bg.js` (hero animation), `site.js` (nav, filters, FAQ)
- `assets/` — portrait + paper PDFs
- `CNAME`, `robots.txt`, `sitemap.xml` — deployment / SEO

## Local preview

```sh
python3 -m http.server 8766
# then open http://localhost:8766
```

## Deploy

Served by GitHub Pages from the `main` branch root. Pushing to `main` publishes.
