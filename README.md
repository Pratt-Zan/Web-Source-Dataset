# Web-Source-Dataset
This project is for the code structure for monthly update of the source in Public com's page source in text.
----
----

# 🌐 Iterative Website Crawler with Incremental Text Storage

## Overview

This project implements an **asynchronous web crawler** using Playwright that extracts **plain text content** from company websites. It is designed with an **incremental update mechanism**, allowing efficient periodic crawling without reprocessing previously visited pages.

The crawler:

* Traverses websites using **Breadth-First Search (BFS)** up to a specified depth
* Extracts and stores **visible text content**
* Maintains a **historical database** to avoid duplicate storage
* Generates **incremental updates** for newly discovered pages


## Key Features

* ⚡ **Asynchronous crawling** using Playwright
* 🔁 **Incremental updates** (only new pages are stored)
* 🌐 **Domain-restricted crawling** (same-site only)
* 🚫 **Smart link filtering** (skips non-HTML resources)
* 📦 **Dual storage system**:

  * Full historical database
  * Incremental update files
* 🧠 **Efficient deduplication** using URL tracking


## Project Structure

```
project/
│
├── Company.json                  # Input: list of company websites
├── json_iter/
│   ├── Company_all_iter_full.json   # Full historical text database
│   └── text_update/
│       └── Company_new_iter_YYYYMMDD.json  # Incremental updates
│
└── crawler.py                    # Main crawler script
```


## Input Data Format

### `Company.json`

```json
[
    {
        "name": "CompanyA",
        "url": "https://www.companya.com"
    },
    {
        "name": "CompanyB",
        "url": "https://www.companyb.com"
    }
]
```


## Output Data Format

### 1. Full Historical Database

**File:** `Company_all_iter_full.json`

```json
{
    "CompanyA": {
        "https://www.companya.com/page1": "text content...",
        "https://www.companya.com/page2": "text content..."
    }
}
```


### 2. Incremental Update File

**File:** `Company_new_iter_YYYYMMDD.json`

```json
{
    "CompanyA": {
        "https://www.companya.com/new-page": "text content..."
    }
}
```


## Installation

### Requirements

* Python 3.8+
* Playwright

### Install dependencies

```bash
pip install playwright
playwright install
```

## Usage

### Step 1: Configure Paths

Update the following variables in `main()`:

```python
input_json_file = 'path/to/Company.json'
output_text_full = 'path/to/Company_all_iter_full.json'
output_text_new_dir = 'path/to/text_update/'
```


### Step 2: Run the crawler

```bash
python crawler.py
```


## Crawling Logic

### BFS Traversal

* Starts from the company homepage
* Crawls up to `max_depth` (default = 2)
* Uses a queue to ensure breadth-first exploration


### Link Filtering

The crawler skips:

* `javascript:`, `mailto:`, `tel:`, anchors
* Static/non-text files:

  * Images (`.jpg`, `.png`, etc.)
  * Documents (`.pdf`, `.docx`, `.xlsx`)
  * Media (`.mp4`, `.zip`, etc.)


### Incremental Mechanism

For each URL:

| Condition                | Action                         |
| ------------------------ | ------------------------------ |
| Already in historical DB | Skip saving, continue crawling |
| New page                 | Extract text and store         |


## Performance Optimizations

* Blocks unnecessary resources:

  * Images
  * CSS
  * Fonts
  * Media
* Uses `domcontentloaded` instead of full page load
* Adds delay (`0.5s`) to reduce server pressure
* Avoids duplicate queueing with `enqueued` set

## Error Handling

Handles common issues such as:

* Download-triggered pages
* Aborted requests (`net::ERR_ABORTED`)
* Timeout errors
* Invalid or inaccessible URLs

## Notes & Limitations

* ⚠️ JavaScript-heavy pages may not fully render content
* ⚠️ Some sites may block automated crawling
* ⚠️ Fixed timeout (15s) may skip slow pages
* ⚠️ Depth limit may miss deeply nested content
* ⚠️ No proxy or user-agent rotation implemented

## Potential Improvements

* Add proxy / anti-bot support
* Support multi-threaded or distributed crawling
* Store metadata (title, timestamp, language)
* Implement change detection (not just new pages)
* Add retry mechanism for failed requests
