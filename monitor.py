import asyncio, yaml, os
from playwright.async_api import async_playwright
import cv2
from skimage.metrics import structural_similarity as ssim
import requests

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
THRESHOLD = 0.98

async def capture(page_cfg):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({
            "width": page_cfg["viewport"][0],
            "height": page_cfg["viewport"][1]
        })
        await page.goto(page_cfg["url"], wait_until="networkidle")
        await page.wait_for_selector(page_cfg["wait_for"])

        for selector in page_cfg["mask"]:
            await page.add_style_tag(content=f"""
                {selector} {{
                    visibility: hidden !important;
                }}
            """)

        img = await page.screenshot(full_page=True)
        await browser.close()
        return img

def diff(prev, curr, out):
    img1 = cv2.imread(prev)
    img2 = cv2.imread(curr)
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, diff = ssim(gray1, gray2, full=True)
    if score < THRESHOLD:
        cv2.imwrite(out, img2)
    return score

async def main():
    os.makedirs("screenshots", exist_ok=True)
    with open("pages.yaml") as f:
        pages = yaml.safe_load(f)["pages"]

    for p in pages:
        name = p["name"].replace(" ", "_")
        prev = f"screenshots/{name}.png"
        curr = f"screenshots/{name}_new.png"

        img = await capture(p)
        open(curr, "wb").write(img)

        if os.path.exists(prev):
            score = diff(prev, curr, prev)
            if score < THRESHOLD:
                requests.post(DISCORD_WEBHOOK, json={
                    "content": f"🚨 Visual change detected on **{p['name']}**\n{p['url']}"
                })

        os.replace(curr, prev)

asyncio.run(main())
