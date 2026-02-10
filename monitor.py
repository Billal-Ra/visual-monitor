import asyncio
import yaml
import os
import cv2
import requests
from playwright.async_api import async_playwright
from skimage.metrics import structural_similarity as ssim

# ===== CONFIG =====
THRESHOLD = 0.98
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# ==================

async def capture(page_cfg):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )

        page = await browser.new_page()

        # Human-like User-Agent
        await page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        })

        await page.set_viewport_size({
            "width": page_cfg["viewport"][0],
            "height": page_cfg["viewport"][1]
        })

        # Safer page load (no networkidle)
        await page.goto(
            page_cfg["url"],
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Optional selector wait
        if page_cfg.get("wait_for"):
            await page.wait_for_selector(
                page_cfg["wait_for"],
                timeout=30000
            )

        # Mask dynamic elements
        for selector in page_cfg.get("mask", []):
            await page.add_style_tag(content=f"""
                {selector} {{
                    visibility: hidden !important;
                }}
            """)

        screenshot = await page.screenshot(full_page=True)
        await browser.close()
        return screenshot


def diff_images(prev_path, curr_path, out_path):
    img1 = cv2.imread(prev_path)
    img2 = cv2.imread(curr_path)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    score, diff = ssim(gray1, gray2, full=True)
    diff = (1 - diff) * 255
    diff = diff.astype("uint8")

    thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(
            img2,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            2
        )

    cv2.imwrite(out_path, img2)
    return score


async def main():
    os.makedirs("screenshots", exist_ok=True)

    with open("pages.yaml") as f:
        pages = yaml.safe_load(f)["pages"]

    for page_cfg in pages:
        name = page_cfg["name"].replace(" ", "_")

        prev = f"screenshots/{name}.png"
        curr = f"screenshots/{name}_new.png"
        diff = f"screenshots/{name}_diff.png"

        screenshot = await capture(page_cfg)

        with open(curr, "wb") as f:
            f.write(screenshot)

        if os.path.exists(prev):
            score = diff_images(prev, curr, diff)

            if score < THRESHOLD:
                requests.post(
                    DISCORD_WEBHOOK,
                    json={
                        "content": (
                            f"🚨 **Visual change detected**\n"
                            f"**{page_cfg['name']}**\n"
                            f"{page_cfg['url']}\n"
                            f"Similarity score: `{score:.4f}`"
                        )
                    },
                    files={
                        "file": open(diff, "rb")
                    }
                )

        os.replace(curr, prev)


if __name__ == "__main__":
    asyncio.run(main())
