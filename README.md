# AID Lab website

Static site for the **AI & Dynamics Group (AID Lab)** at the University of Rochester,
led by Yuanzhao Zhang. Plain HTML/CSS/vanilla JS — no build step.

**Live:** https://lab.y-zhang.com

## Structure

- `*.html` — one file per page (home, research, people, publications, news, join, 404)
- `styles.css` — all styling and design tokens
- `js/` — `logo.js` (SVG mark/wordmark, styles intentionally inline),
  `lab-visuals.js` (hand-drawn research SVG renderers), `draw-visuals.js`
  (draws them onto `svg.lab-visual` elements), `rough.js` (vendored
  RoughJS v4.6.6, MIT), `flow-bg.js` (hero animation), `site.js`
  (nav, filters, FAQ)
- `assets/` — portrait, og/social image, icons, paper PDFs
- `CNAME`, `robots.txt`, `sitemap.xml`, `favicon.ico` — deployment / SEO

## Local preview

```sh
python3 -m http.server 8766
# then open http://localhost:8766
```

## Deploy

Served by GitHub Pages from the `main` branch root. Pushing to `main` publishes.
