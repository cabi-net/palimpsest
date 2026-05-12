import asyncio
import requests
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

async def scrape_google():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await page.goto(
            "https://support.google.com/assistant/answer/11091015?hl=en",
            wait_until="networkidle",
            timeout=30000
        )
        await page.wait_for_timeout(3000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    chunks = []
    for tag in soup.find_all(["h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)
    return "\n\n".join(chunks)


async def scrape_meta():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await page.goto(
            "https://privacycenter.instagram.com/privacy/genai/",
            wait_until="networkidle",
            timeout=30000
        )
        await page.wait_for_timeout(4000)

        # click all accordion buttons to expand hidden content
        buttons = await page.query_selector_all('[role="button"]')
        for button in buttons:
            try:
                expanded = await button.get_attribute("aria-expanded")
                if expanded == "false":
                    await button.click()
                    await page.wait_for_timeout(500)
            except:
                pass

        await page.wait_for_timeout(2000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    chunks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li", "span"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 60:
            chunks.append(text)

    # deduplicate while preserving order
    seen = set()
    unique = []
    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique.append(chunk)

    return "\n\n".join(unique)

async def scrape_microsoft():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await page.goto(
            "https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy",
            wait_until="networkidle",
            timeout=30000
        )
        await page.wait_for_timeout(4000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # target the main article content, ignore nav/sidebar
    article = soup.find("main") or soup
    chunks = []
    for tag in article.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)

    seen = set()
    unique = []
    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique.append(chunk)

    return "\n\n".join(unique)


def scrape_openai_wayback():
    # CDX queries the raw capture index, unlike the `available` endpoint which
    # returns empty when the live site's robots.txt blocks the path.
    try:
        cdx = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url": "openai.com/policies/data-processing-addendum/",
                "limit": "-1",
                "output": "json",
                "filter": "statuscode:200",
            },
            timeout=30,
        )
        if not cdx.text.strip():
            return "Wayback CDX returned empty response — try again later"
        rows = cdx.json()
    except Exception as e:
        return f"Wayback CDX error: {str(e)}"

    if len(rows) < 2:
        return "No snapshot available"

    timestamp, original = rows[1][1], rows[1][2]
    snapshot_url = f"https://web.archive.org/web/{timestamp}/{original}"

    try:
        page = requests.get(snapshot_url, timeout=30)
        soup = BeautifulSoup(page.content, "html.parser")
    except Exception as e:
        return f"Failed to fetch snapshot: {str(e)}"

    chunks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)

    header = f"[Wayback snapshot: {timestamp}]\n[URL: {snapshot_url}]\n\n"
    return header + "\n\n".join(chunks)


def save_snapshot(name, content):
    folder = f"snapshots/{name}"
    os.makedirs(folder, exist_ok=True)
    filepath = f"{folder}/{DATE}.txt"

    if os.path.exists(filepath):
        time_str = datetime.now(timezone.utc).strftime("%H%M")
        catch_folder = f"snapshots/catches/{name}"
        os.makedirs(catch_folder, exist_ok=True)
        catch_path = f"{catch_folder}/{DATE}-{time_str}.txt"
        with open(catch_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Already scraped today — saved as catch: {catch_path}")
        return

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filepath}")


async def main():
    print("Scraping Google...")
    save_snapshot("google", await scrape_google())

    print("Scraping Meta...")
    save_snapshot("meta", await scrape_meta())

    print("Scraping Microsoft...")
    save_snapshot("microsoft", await scrape_microsoft())

    print("Scraping OpenAI via Wayback Machine...")
    openai_content = scrape_openai_wayback()
    if openai_content.startswith(("Wayback", "No snapshot", "Failed")):
        print(f"Skipping save: {openai_content}")
    else:
        save_snapshot("openai", openai_content)

asyncio.run(main())