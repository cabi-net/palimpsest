# palimpsest
 
> writing material (such as a parchment or tablet) used one or more times after earlier writing has been erased[^1]

 
An automated archive that watches the language of institutional AI and data privacy disclosures over time, and makes their changes visible (diff viewer to be implemented).
 
---
## what it watches
 
| institution | page | method |
|---|---|---|
| Google | [How Google Assistant works with your data](https://support.google.com/assistant/answer/11091015?hl=en) | Playwright |
| Meta | [How Meta uses information for generative AI models](https://privacycenter.instagram.com/privacy/genai/) | Playwright |
| Microsoft | [Data, privacy, and security for Azure OpenAI](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy) | Playwright |
| OpenAI | [Data Processing Addendum](https://openai.com/policies/data-processing-addendum/) | Wayback Machine |

---

## how it works

A GitHub Actions workflow runs every Monday at 9am UTC. It scrapes each target page, extracts the meaningful text, and commits a dated snapshot to this repository. 

OpenAI's policy pages actively block automated access. Their snapshots are retrieved via the Internet Archive instead — a layer of mediation that is itself part of the record.

If a snapshot file for the current date already exists when the script runs — for instance, if it is triggered more than once on the same day — the new output is saved to `snapshots/catches/{institution}/YYYY-MM-DD-HHMM.txt` instead of overwriting the canonical snapshot.

---

## structure

```
snapshots/
├── google/
│     YYYY-MM-DD.txt
├── meta/
│     YYYY-MM-DD.txt
├── microsoft/
│     YYYY-MM-DD.txt
├── openai/
│     YYYY-MM-DD.txt
└── catches/
```

---
 
## technical
 
Built with Python, Playwright, BeautifulSoup, and GitHub Actions. There is no database - the repository history is the data structure.

---

## status
 
Began archiving: March 2026  
Snapshot frequency: weekly  
Diff viewer: forthcoming

---

## a note on infrastructure

This project runs on GitHub, which is owned by Microsoft. Microsoft is one of the four companies whose rhetorical behavior this archive documents. This is not a contradiction to resolve or hide; it is part of the record.

[^1]: [*Merriam-Webster*](https://www.merriam-webster.com/dictionary/palimpsest)
