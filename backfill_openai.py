import requests
from bs4 import BeautifulSoup

BACKFILLS = [
    ("20260329215201", "2026-03-30"),
    ("20260402150529", "2026-04-06"),
    ("20260505125543", "2026-05-04"),
]

ORIGINAL = "https://openai.com/policies/data-processing-addendum/"

for timestamp, target_date in BACKFILLS:
    snapshot_url = f"https://web.archive.org/web/{timestamp}/{ORIGINAL}"
    page = requests.get(snapshot_url, timeout=60)
    soup = BeautifulSoup(page.content, "html.parser")

    chunks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:
            chunks.append(text)

    header = f"[Wayback snapshot: {timestamp}]\n[URL: {snapshot_url}]\n\n"
    body = header + "\n\n".join(chunks)

    path = f"snapshots/openai/{target_date}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"wrote {path} ({len(body)} chars)")
