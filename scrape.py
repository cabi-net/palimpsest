import asyncio
import requests
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

TARGETS = {
    "google": {
        "url": "https://support.google.com/assistant/answer/11091015?hl=en",
        "selectors": [
            "h2", "h3", "p", "li"
        ]
    },
    "meta": {
        "url": "https://privacycenter.instagram.com/privacy/genai/",
        "selectors": [
            "h1", "h2", "h3", "p", "li"
        ]
    }
}

async def scrape_with_playwright(name, config):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await page.goto(config["url"], wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    chunks = []
    for tag in soup.find_all(config["selectors"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)

    return "\n\n".join(chunks)


def scrape_openai_wayback():
    url = "http://archive.org/wayback/available?url=openai.com/policies/data-processing-addendum/"
    try:
        response = requests.get(url, timeout=15)
        if not response.text.strip():
            return "Wayback API returned empty response — try again later"
        data = response.json()
    except Exception as e:
        return f"Wayback API error: {str(e)}"

    snapshot = data.get("archived_snapshots", {}).get("closest", {})

    if not snapshot or not snapshot.get("available"):
        return "No snapshot available"

    snapshot_url = snapshot["url"]
    try:
        page = requests.get(snapshot_url, timeout=15)
        soup = BeautifulSoup(page.content, "html.parser")
    except Exception as e:
        return f"Failed to fetch snapshot: {str(e)}"

    chunks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)

    snapshot_date = snapshot.get("timestamp", "unknown")
    header = f"[Wayback snapshot: {snapshot_date}]\n[URL: {snapshot_url}]\n\n"
    return header + "\n\n".join(chunks)


def save_snapshot(name, content):
    folder = f"snapshots/{name}"
    os.makedirs(folder, exist_ok=True)
    filepath = f"{folder}/{DATE}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filepath}")


async def main():
    for name, config in TARGETS.items():
        print(f"Scraping {name}...")
        content = await scrape_with_playwright(name, config)
        save_snapshot(name, content)

    print("Scraping OpenAI via Wayback Machine...")
    content = scrape_openai_wayback()
    save_snapshot("openai", content)

asyncio.run(main())