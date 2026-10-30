"""Convert the rendered figure PNGs into the WebP files the site serves.

Reads   figures-src/<theme>/out/<theme>.png   (800x800, written by each theme's render.py)
Writes  assets/figures/<theme>.webp           (Pillow WebP, quality 90, method 6)

Run from anywhere:  python3 -I figures-src/export_webp.py [theme ...]
With no arguments it exports all three themes that have a rendered PNG.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets', 'figures')
THEMES = ['ml-for-dynamics', 'physics-of-ai', 'networks-emergence']


def export(theme):
    src = os.path.join(HERE, theme, 'out', theme + '.png')
    if not os.path.exists(src):
        print(f'skip {theme}: {os.path.relpath(src)} not found (run {theme}/render.py first)')
        return
    im = Image.open(src).convert('RGB')
    if im.size != (800, 800):
        sys.exit(f'{theme}: expected 800x800, got {im.size}')
    dst = os.path.join(ASSETS, theme + '.webp')
    im.save(dst, 'WEBP', quality=90, method=6)
    print(f'{theme}: wrote {os.path.relpath(dst)} ({os.path.getsize(dst)} bytes)')


if __name__ == '__main__':
    os.makedirs(ASSETS, exist_ok=True)
    for t in (sys.argv[1:] or THEMES):
        if t not in THEMES:
            sys.exit(f'unknown theme {t!r}; choose from {THEMES}')
        export(t)
