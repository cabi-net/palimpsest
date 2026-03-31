import difflib
import html
import os
from datetime import datetime, timezone

INSTITUTIONS = ["google", "meta", "microsoft", "openai"]

INSTITUTION_LABELS = {
    "google": "Google",
    "meta": "Meta",
    "microsoft": "Microsoft",
    "openai": "OpenAI",
}

ERROR_PREFIXES = (
    "Wayback API error:",
    "No snapshot available",
    "Failed to fetch snapshot:",
    "Wayback API returned empty",
)


def is_valid(paragraphs):
    if len(paragraphs) < 3:
        return False
    if any(paragraphs[0].startswith(p) for p in ERROR_PREFIXES):
        return False
    return True


def load_snapshots(institution):
    folder = os.path.join("snapshots", institution)
    if not os.path.isdir(folder):
        return []
    entries = []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".txt") or len(filename) != 14:
            continue
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            continue
        date_str = filename[:-4]
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
        if is_valid(paragraphs):
            entries.append((date_str, paragraphs))
    return entries


def strip_wayback_header(paragraphs):
    meta = None
    paras = list(paragraphs)
    if paras and paras[0].startswith("[Wayback snapshot:"):
        meta = paras.pop(0)
        if paras and paras[0].startswith("[URL:"):
            paras.pop(0)
    return paras, meta


def diff_paragraphs(old, new):
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        ops.append({
            "tag": tag,
            "old": old[i1:i2],
            "new": new[j1:j2],
            "count": i2 - i1,
        })
    return ops


def render_ops(ops):
    parts = []
    only_equal = all(op["tag"] == "equal" for op in ops)

    if only_equal:
        total = sum(op["count"] for op in ops)
        parts.append(f'<div class="context-gap no-changes">[ no changes detected &mdash; {total} paragraph{"s" if total != 1 else ""} unchanged ]</div>')
        return "".join(parts)

    for i, op in enumerate(ops):
        tag = op["tag"]
        is_first = i == 0
        is_last = i == len(ops) - 1

        if tag == "equal":
            if is_first or is_last:
                continue
            n = op["count"]
            parts.append(f'<div class="context-gap">[ {n} unchanged paragraph{"s" if n != 1 else ""} ]</div>')
        elif tag == "delete":
            for para in op["old"]:
                parts.append(f'<div class="para deleted">{html.escape(para)}</div>')
        elif tag == "insert":
            for para in op["new"]:
                parts.append(f'<div class="para added">{html.escape(para)}</div>')
        elif tag == "replace":
            for para in op["old"]:
                parts.append(f'<div class="para deleted">{html.escape(para)}</div>')
            for para in op["new"]:
                parts.append(f'<div class="para added">{html.escape(para)}</div>')

    return "".join(parts)


def render_institution(name, pairs):
    label = INSTITUTION_LABELS.get(name, name.title())
    periods = []
    for date_old, date_new, ops, meta in pairs:
        meta_html = f'<p class="wayback-meta">{html.escape(meta)}</p>' if meta else ""
        body = render_ops(ops)
        periods.append(f'<div class="diff-period"><p class="daterange">{date_old} &mdash; {date_new}</p>{meta_html}<div class="diff-body">{body}</div></div>')
    return f"""
<section class="institution" id="{name}">
  <h2>{label}</h2>
  {"".join(periods)}
</section>"""


def render_no_diff_institution(name, reason):
    label = INSTITUTION_LABELS.get(name, name.title())
    return f"""
<section class="institution" id="{name}">
  <h2>{label}</h2>
  <p class="no-diff">{reason}</p>
</section>"""


def css():
    return """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #f9f7f4;
      color: #1a1a1a;
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 1rem;
      line-height: 1.65;
      padding: 3rem 1.5rem;
    }

    .wrap {
      max-width: 860px;
      margin: 0 auto;
    }

    header {
      border-bottom: 1px solid #ddd;
      margin-bottom: 3rem;
      padding-bottom: 1.5rem;
    }

    header h1 {
      font-size: 1.4rem;
      font-weight: normal;
      letter-spacing: 0.12em;
      text-transform: lowercase;
    }

    header .subtitle {
      color: #666;
      font-size: 0.9rem;
      margin-top: 0.3rem;
    }

    header .generated {
      color: #aaa;
      font-family: 'Courier New', monospace;
      font-size: 0.75rem;
      margin-top: 0.5rem;
    }

    .institution {
      margin-bottom: 3.5rem;
    }

    .institution h2 {
      font-size: 0.8rem;
      font-weight: normal;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #444;
      margin-bottom: 0.3rem;
    }

    .daterange {
      font-family: 'Courier New', monospace;
      font-size: 0.78rem;
      color: #999;
      margin-bottom: 1rem;
    }

    .wayback-meta {
      font-family: 'Courier New', monospace;
      font-size: 0.72rem;
      color: #bbb;
      margin-bottom: 0.75rem;
    }

    .diff-period {
      margin-bottom: 2rem;
    }

    .diff-period + .diff-period {
      border-top: 1px dashed #e0dbd5;
      padding-top: 1.5rem;
    }

    .diff-body {
      border-top: 1px solid #e8e4df;
      padding-top: 1rem;
    }

    .para {
      padding: 0.55em 1em;
      margin: 0.2em 0;
      border-left: 3px solid transparent;
      font-size: 0.92rem;
    }

    .deleted {
      background: #fdf0ef;
      border-left-color: #c0392b;
      color: #7a2a25;
    }

    .added {
      background: #f0f7f0;
      border-left-color: #27ae60;
      color: #1e5c3a;
    }

    .context-gap {
      color: #bbb;
      font-size: 0.75rem;
      font-style: italic;
      padding: 0.5em 1em;
      margin: 0.3em 0;
    }

    .no-changes {
      color: #ccc;
    }

    .no-diff {
      color: #aaa;
      font-style: italic;
      font-size: 0.9rem;
    }

    footer {
      border-top: 1px solid #ddd;
      margin-top: 4rem;
      padding-top: 1.5rem;
      font-size: 0.78rem;
      color: #bbb;
    }
    """


def render_html(sections, generated_at):
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>palimpsest</title>
  <style>{css()}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>palimpsest</h1>
    <p class="subtitle">language changes in AI and data privacy disclosures</p>
    <p class="generated">generated {generated_at}</p>
  </header>
  <main>
    {body}
  </main>
  <footer>
    each section shows the diff between the two most recent snapshots for that institution.
    snapshots are collected weekly. the git history is the archive.
  </footer>
</div>
</body>
</html>"""


def main():
    sections = []

    for institution in INSTITUTIONS:
        snapshots = load_snapshots(institution)

        if len(snapshots) < 2:
            if len(snapshots) == 1:
                date = snapshots[0][0]
                reason = f"Only one valid snapshot available ({date}). Diff will appear after the next archive capture."
            else:
                reason = "No valid snapshots yet."
            sections.append(render_no_diff_institution(institution, reason))
            continue

        pairs = []
        for (date_old, paras_old), (date_new, paras_new) in zip(snapshots, snapshots[1:]):
            paras_old, _ = strip_wayback_header(paras_old)
            paras_new, meta = strip_wayback_header(paras_new)
            ops = diff_paragraphs(paras_old, paras_new)
            pairs.append((date_old, date_new, ops, meta))

        sections.append(render_institution(institution, pairs))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    output = render_html(sections, generated_at)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(output)

    print("Saved: index.html")


main()
