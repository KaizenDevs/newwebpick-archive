#!/usr/bin/env python3
"""Screenshot first frame of SWFs via headless Chromium + Ruffle.

Run a static server at the repo root first (not `yarn dev`, which only
serves site/): `python3 -m http.server 8080`
"""

import asyncio, os, sys
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:8080"
COVERS_DIR = os.path.join(os.path.dirname(__file__), "..", "site", "covers")

# Only capture issues that don't have good covers yet
TARGETS = [f"{i:02d}" for i in range(1, 17)]  # 01–16

HTML = """<!DOCTYPE html>
<html>
<head>
<script src="{base}/node_modules/@ruffle-rs/ruffle/ruffle.js"></script>
<style>
  body {{ margin:0; background:#111; }}
  ruffle-player {{ width:600px; height:450px; display:block; }}
</style>
</head>
<body>
<script>
window.RufflePlayer = window.RufflePlayer || {{}};
</script>
<script src="https://unpkg.com/@ruffle-rs/ruffle"></script>
<div id="player"></div>
<script>
  const ruffle = window.RufflePlayer.newest();
  const player = ruffle.createPlayer();
  player.style.width = "600px";
  player.style.height = "450px";
  document.getElementById("player").appendChild(player);
  player.load("{swf_url}");
  window._player = player;
</script>
</body>
</html>"""

async def screenshot_issue(page, num):
    out = os.path.join(COVERS_DIR, f"cover_{num}.png")
    url = f"{BASE_URL}/scripts/screenshot.html?n={num}"

    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(5000)
    # Click to dismiss Ruffle's "click to play" screen
    try:
        await page.locator("ruffle-player").click(timeout=5000)
    except:
        pass
    # Wait for first frame to render
    await page.wait_for_timeout(15000)

    el = page.locator("ruffle-player")
    try:
        await el.screenshot(path=out)
        print(f"[OK]  {num} → {out}")
    except Exception as e:
        # Fallback: screenshot full page
        await page.screenshot(path=out, clip={"x":0,"y":0,"width":600,"height":450})
        print(f"[FALLBACK] {num} → {out}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 600, "height": 450})

        for num in TARGETS:
            await screenshot_issue(page, num)

        await browser.close()

asyncio.run(main())
