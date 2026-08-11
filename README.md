# YouParts — DIY Manifest Planner

> **From Watch Later to Built.** Turn YouTube build series into a comprehensive Bill of Materials.

YouParts is an AI-powered **Streamlit** app that ingests YouTube playlists from DIY hardware build series (e.g. a force-feedback steering wheel + clutch pedal for BeamNG.drive), screens each video for relevance, and extracts a verified component manifest (BOM) with logic-gap warnings, external resource links, and regional price search.

---
<img width="50%" height="50%" alt="image" src="https://github.com/user-attachments/assets/d987fdc4-f08c-42ee-bfdf-8621f5672099" />


## Summary

* **Ingest** YouTube videos/playlists via `yt-dlp` (metadata: title, description, duration, uploader).
* **Screen** each video against your target build with a fast Groq model. Videos with a relevance score of **≥ 0.65** are kept, with live progress displayed.
* **Extract** a structured BOM with a stronger Groq model under strict **anti-hallucination rules** — only explicitly stated quantities/specs are recorded; critical missing specs become **logic-gap warnings**.
* **Aggregate** a master manifest containing the component checklist, logic-gap directives, CAD/resource links, and regional price searches for **any online stores**.

---

## Features

* **Hallucination-guarded extraction** — no invented parts, dimensions, quantities, or specifications.
* **Logic-gap detection** — flags missing information such as bolt lengths, unstated tolerances, or other requirements needed to actually reproduce a build.
* **Regional price search** — per-store toggles with fallback search links.
* **Optional Playwright stealth scraper template** — foundation for real listing scraping.
* **Bento-card navigation** — clean navigation between workspace sections.
* **Live pipeline progress** — tracks screening and BOM extraction as they happen.

---

## How It Works

```text
YouTube URLs
     ↓
yt-dlp ingest
     ↓
Relevance screening (Groq)
     ↓
BOM extraction (Groq)
     ↓
Master manifest
     ↓
Workspace
```

### 1. Ingest

`PlaylistParser` + `YouTubeDataFetcher` expand playlists, fetch video metadata, and deduplicate videos.

### 2. Screen

`RelevanceFilterEngine` scores each video against the user's build focus. Videos meeting the relevance threshold are passed to extraction.

### 3. Extract

`BOMExtractorEngine` processes each relevant video and produces a validated `VideoBOMExtraction`.

The extraction layer is deliberately conservative: if a component, quantity, dimension, or specification is not explicitly supported by the source material, it should not be invented.

### 4. Aggregate

Individual extractions are combined into:

* `parts_manifest`
* `external_resources`
* `logic_gaps`

### 5. Workspace

The resulting workspace lets you:

* Browse and check off components.
* Review logic gaps and warnings.
* Open CAD and external resource links.
* Select components for regional price searches.
* Compare available regional-store search results.

---

## Project Layout

```text
YouParts/
├── app.py                         # Streamlit entry point, pipeline runner, footer
│
├── config/
│   ├── settings.py                # Environment + persisted config
│   │                                # Models, cooldowns, scraper toggles
│   └── prompts.py                 # System prompts + Pydantic extraction schemas
│
├── src/
│   ├── ingestor/                  # YouTube ingestion (yt-dlp)
│   ├── ai_engine/                 # Relevance screening + BOM extraction (Groq)
│   ├── scrapers/                  # AliExpress / Shopee / Lazada + stealth template
│   │
│   └── ui/
│       └── components/            # Navbar, landing, workspace, settings drawer, theme
│
├── shaders/
│   └── PaperShader.jsx            # Reference only (not executed by Streamlit)
│
├── assets/
│   ├── yp-nobg.png                # Logo
│   ├── yp.png                     # Logo variant
│   └── favicon.ico                # Favicon
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Setup

### Requirements

* **Python 3.10+**
* A **Groq API key**
* Optional: **Playwright** for the stealth scraper template

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd YouParts
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional — Install Playwright

If you want to experiment with the real-listing scraper template:

```bash
playwright install chromium
```

### 5. Configure your Groq API key

Copy `.env.example` to `.env` and set:

```env
GROQ_API_KEY=<your-key>
```

Alternatively, enter the key through the in-app **Configuration & API Keys** drawer.

### 6. Run YouParts

```bash
streamlit run app.py
```

---

## Operation

### Landing Page

Paste one URL per line. Both **YouTube playlists and individual videos** are supported.

Set your build focus and click:

> **EXTRACT PARTS MANIFEST**

A live progress bar tracks:

1. Video ingestion
2. Relevance screening
3. BOM extraction
4. Manifest aggregation

### Workspace

Once processing completes, the generated manifest opens in the workspace.

The workspace is organized into four main bento-card sections:

#### Bill of Materials

A categorized component checklist containing the parts extracted from the source videos.

#### Logic Gaps & Warnings

Critical information that was missing, ambiguous, or insufficiently specified in the source material.

Examples include:

* Missing bolt lengths
* Unspecified tolerances
* Missing dimensions
* Components referenced but not adequately specified

#### CAD & Resource Links

External resources discovered during extraction, including CAD files, build references, documentation, and other useful links.

#### Regional Price Search

Select a component and use **Search Regional Stores** to search any marketplace, right now the web-app comes with:

* AliExpress
* Shopee
* Lazada

Individual stores can be enabled or disabled through the settings drawer.

### Settings Drawer

The landing-page settings drawer allows you to configure:

* Groq API key
* API request cooldown
* AliExpress integration
* Shopee integration
* Lazada integration

Persisted settings are stored in:

```text
config/youparts_config.json
```

---

## Configuration — What to Tweak

### Groq API Key

Configure through the settings drawer or `.env`:

```env
GROQ_API_KEY=<your-key>
```

### Models

Edit `config/settings.py`:

```python
RELEVANCE_MODEL
EXTRACTION_MODEL
```

`RELEVANCE_MODEL` handles fast screening, while `EXTRACTION_MODEL` handles grounded BOM extraction.

Both can be swapped for any compatible Groq-supported model.

### Relevance Threshold

The default relevance threshold is **0.65**.

It can be adjusted in:

```text
src/ai_engine/relevance_filter.py
```

Look for:

```python
filter_playlist(..., threshold=0.65)
```

### Rate Limits

In `config/settings.py`:

```python
REQUEST_DELAY_SECONDS = 1.5
MAX_RETRIES = 3
```

These are particularly useful when working around Groq free-tier rate limits and cooldowns.

### Scraper Toggles (These are examples, tweak these)

Enable or disable individual regional stores through:

```text
ENABLE_ALIEXPRESS
ENABLE_SHOPEE
ENABLE_LAZADA
```

### Branding

Replace the files in `assets/` to customize the branding:

```text
assets/yp-nobg.png
assets/yp.png
assets/favicon.ico
```

### Shader Intensity

The paper-drift shader can be adjusted through the `shader_html` canvas configuration in `app.py`.

Current opacity:

```text
opacity: 0.6
```

### Prompts / Extraction Schema

The system prompts and Pydantic extraction models live in:

```text
config/prompts.py
```

Edit these carefully. The extraction schema is coupled to both the AI pipeline and the UI.

---

## What Does NOT Need Tweaking

### Default Pipeline Flow

The default pipeline works out of the box:

```text
ingest → screen → extract → aggregate
```

### Extraction Schemas

The following models define the structure expected by the extraction pipeline and UI:

```text
BOMItem
ExternalResource
VideoBOMExtraction
```

Keep their field shapes stable unless you are intentionally changing the pipeline and UI together.

### Configuration Persistence

Configuration is automatically loaded and saved through:

```text
config/youparts_config.json
.env
```

### Theme CSS

`src/ui/components/theme.py` contains the styling for the paper aesthetic.

It generally does not need to be modified unless you want to restyle the application.

---

## Anti-Hallucination

YouParts is designed around a simple principle:

> **If the source doesn't say it, YouParts shouldn't pretend it does. Otherwise a wrong source might mess up your whole project.**

The extraction pipeline intentionally distinguishes between:

* **Explicitly stated information** — safe to include in the BOM.
* **Ambiguous information** — should be surfaced for review.
* **Missing critical information** — becomes a logic gap.
* **Inferred information** — should not silently become a component specification.

This is important for DIY hardware builds where a seemingly minor missing specification — such as a fastener length, material thickness, shaft diameter, or tolerance — can make the difference between a useful build guide and an incomplete parts list.

---

## Security Notes

### Never Commit API Keys

Do **not** commit real API keys to Git.

Your `.env` should contain the real key locally:

```env
GROQ_API_KEY=<your-key>
```

But the repository should only contain a placeholder in `.env.example`:

```env
GROQ_API_KEY=
```

### Add Local Configuration to `.gitignore`

Make sure your `.gitignore` excludes:

```gitignore
.env
config/youparts_config.json
```

---

## Roadmap / Future Work

Potential areas for further development include:

* Real marketplace listing scraping through Playwright.
* More robust source verification across multiple videos.
* Better deduplication and component normalization. ✔️
* Confidence scoring for extracted components.
* Cross-video contradiction detection.
* More regional marketplaces.
* Export to CSV / JSON / shopping lists.✔️
* Build-stage grouping and dependency tracking.✔️

---

## Tech Stack

| Layer                 | Technology                   |
| --------------------- | ---------------------------- |
| Frontend / App        | Streamlit                    |
| Language              | Python 3.10+                 |
| Video ingestion       | yt-dlp                       |
| AI                    | Groq                         |
| Structured extraction | Pydantic                     |
| Marketplace scraping  | Playwright / custom scrapers |
| Styling               | Streamlit CSS                |
| Visual effects        | WebGL / Canvas shader        |
| Data source           | YouTube                      |

---

## License

```text
MIT License
```
