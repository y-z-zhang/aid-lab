# AI & Dynamics Group website

Static site for the **AI & Dynamics Group** at the University of Rochester,
led by Yuanzhao Zhang. Plain HTML/CSS/vanilla JS — no build step.

**Live:** https://lab.y-zhang.com

## Structure

- `*.html` — one file per page (home, research, people, publications, news, join, 404);
  news is currently hidden from the nav and sitemap (commented-out links)
- `styles.css` — all styling and design tokens
- `js/` — `logo.js` (SVG mark/wordmark, styles intentionally inline),
  `flow-bg.js` (hero animation), `site.js` (nav, filters, FAQ)
- `assets/` — portrait, og/social image, icons, paper PDFs, `figures/`
  (one figure per research theme, cropped from our papers; credits on the pages)
- `CNAME`, `robots.txt`, `sitemap.xml`, `favicon.ico` — deployment / SEO

## Local preview

```sh
python3 -m http.server 8766
# then open http://localhost:8766
```

## Deploy

Served by GitHub Pages from the `main` branch root. Pushing to `main` publishes.
