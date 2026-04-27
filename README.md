# Web-Source-Dataset
This project is for the code structure for monthly update of the source in Public com's page source in text.

----

# 🌐 Iterative Website Crawler with Incremental Text Storage

## Overview

This project implements an **asynchronous, domain-restricted web crawler** using Playwright for large-scale extraction of **plain textual content from company websites**. The primary objective is to build and maintain a continuously growing **textual database of corporate web disclosures**, while minimizing redundant computation through an **incremental update framework**.

Unlike naive crawlers that repeatedly scrape the same pages, this system is designed to:

* **Persist historical crawl results**
* **Detect and skip previously processed URLs**
* **Only store newly discovered content in each run**

This makes it particularly suitable for **longitudinal data collection tasks**, such as tracking changes in corporate disclosures, ESG communication, or investor-facing information over time.

The crawler follows a **Breadth-First Search (BFS)** strategy with a configurable depth limit, ensuring structured and controlled exploration of each website while avoiding excessive crawling.

## Key Features

This crawler includes several design choices aimed at balancing **efficiency, scalability, and robustness**:

* **Asynchronous Execution (Playwright-based)**
  The crawler leverages `asyncio` and Playwright’s async API to efficiently handle page navigation and content extraction without blocking execution.

* **Incremental Crawling Architecture**
  A dual-database system is used:

  * A **full historical database** storing all previously crawled pages
  * A **run-specific incremental database** storing only newly discovered pages
    This significantly reduces redundant I/O and computation in repeated runs.

* **Domain-Constrained Crawling**
  The crawler strictly limits traversal to the **same domain as the starting URL**, preventing unintended expansion into external sites.

* **Content-Focused Extraction**
  Only **visible text (`document.body.innerText`)** is extracted, ensuring that the stored data is suitable for downstream NLP or textual analysis.

* **Resource Optimization**
  Non-essential resources (images, CSS, fonts, media) are blocked at the network level to:

  * Reduce bandwidth usage
  * Improve crawling speed
  * Lower memory overhead

* **Duplicate Avoidance Mechanisms**
  Two sets are maintained:

  * `visited`: tracks already processed pages
  * `enqueued`: prevents duplicate queue insertion
    This ensures efficient traversal without redundant operations.

## Project Structure

The project is organized to clearly separate **input configuration**, **persistent storage**, and **runtime outputs**:

```
project/
│
├── Company.json
│   Input file containing company names and their homepage URLs.
│
├── json_iter/
│   ├── Company_all_iter_full.json
│   │   Persistent full database storing all historical crawl results.
│   │
│   └── text_update/
│       └── Company_new_iter_YYYYMMDD.json
│           Incremental output file generated for each run,
│           containing only newly discovered pages.
│
└── crawler.py
    Main script implementing crawling logic, data handling,
    and incremental update workflow.
```

This structure allows the crawler to be executed repeatedly over time while maintaining a clean separation between **historical data** and **newly collected data**.

## Input Data Format

### `Company.json`

The crawler expects a JSON file containing a list of target websites. Each entry represents a company and includes:

* `name`: Identifier used as a key in the output database
* `url`: The starting point for crawling (homepage or portal page)

Example:

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

### Important Notes on Input

* URLs should be **fully qualified** (including `https://`)
* Each company should have a **unique name** to avoid overwriting data
* The crawler assumes that each URL represents a **distinct domain root**

## Output Data Format

The system produces two types of outputs: a **persistent full dataset** and a **run-specific incremental dataset**.

### 1. Full Historical Database

**File:** `Company_all_iter_full.json`

This file serves as the **master database**, continuously updated after each run. It stores all previously crawled pages and their extracted text content.

Structure:

```json
{
    "CompanyA": {
        "https://www.companya.com/page1": "Full text content of page1...",
        "https://www.companya.com/page2": "Full text content of page2..."
    }
}
```

Key characteristics:

* Organized by **company name**
* Each URL maps directly to its **plain text content**
* Used as the **reference for deduplication** in future runs

### 2. Incremental Update File

**File:** `Company_new_iter_YYYYMMDD.json`

This file contains **only the pages newly discovered during the current execution**.

Structure:

```json
{
    "CompanyA": {
        "https://www.companya.com/new-page": "Text content..."
    }
}
```

Key characteristics:

* Generated with a **date-based filename**
* Includes only **previously unseen URLs**
* Empty company entries are automatically removed for cleanliness

This design enables efficient tracking of **what changed between runs**, which is critical for time-series analysis.

## Installation

### Requirements

To run the crawler, the following environment is required:

* **Python 3.8 or higher**
* **Playwright** (for browser automation)

### Install Dependencies

Install Playwright via pip:

```bash
pip install playwright
```

Then install the required browser binaries:

```bash
playwright install
```

This step is necessary for Playwright to launch a headless browser instance.

## Usage

### Step 1: Configure File Paths

Before running the script, update the file paths in the `main()` function:

```python
input_json_file = 'path/to/Company.json'
output_text_full = 'path/to/Company_all_iter_full.json'
output_text_new_dir = 'path/to/text_update/'
```

Make sure:

* The input file exists
* Output directories are writable
* Paths are compatible with your operating system

### Step 2: Execute the Script

Run the crawler using:

```bash
python crawler.py
```

During execution, the script will:

1. Load the company list
2. Load (or initialize) the historical database
3. Crawl each website sequentially
4. Update both full and incremental datasets

## Crawling Logic

### Breadth-First Search (BFS) Strategy

The crawler uses a BFS approach to systematically explore each website:

* Starts from the **homepage**
* Expands outward level by level
* Stops when reaching `max_depth` (default: 2)

This ensures:

* Controlled crawl scope
* Better coverage of high-level pages
* Reduced risk of deep, irrelevant traversal

### URL Processing Workflow

For each page:

1. Check if the URL has already been visited
2. Determine whether it exists in the historical database
3. If new:

   * Extract visible text
   * Store in both full and incremental databases
4. Extract all anchor (`<a>`) links
5. Filter and normalize URLs
6. Add unseen links to the queue

### Link Filtering Rules

The crawler excludes:

* Non-navigable links:

  * `javascript:`
  * `mailto:`
  * `tel:`
  * anchor links (`#`)

* Non-text resources:

  * Images (`.jpg`, `.png`, `.gif`)
  * Documents (`.pdf`, `.docx`, `.xlsx`)
  * Media (`.mp4`, `.zip`, `.exe`)
  * Stylesheets (`.css`)

This ensures the crawler focuses only on **HTML pages with meaningful textual content**.

### Domain Restriction

Only links that match the **original domain** are followed. This is enforced by comparing:

```python
urlparse(url).netloc
```

This prevents:

* Crawling external websites
* Data contamination across domains
* Uncontrolled crawl expansion

## Performance Optimizations

Several optimizations are implemented to improve runtime efficiency:

* **Resource Blocking**
  The crawler intercepts network requests and blocks:

  * Images
  * Stylesheets
  * Fonts
  * Media
    This significantly reduces load time and bandwidth usage.

* **Lightweight Page Load Strategy**
  Uses `wait_until="domcontentloaded"` instead of full page load to speed up navigation.

* **Rate Limiting**
  A short delay (`0.5 seconds`) is introduced between requests to:

  * Reduce server load
  * Lower risk of being blocked

* **Queue Deduplication**
  The `enqueued` set ensures that each URL is only added to the queue once.

* **Incremental Saving**
  The full database is written to disk after each site is processed, reducing the risk of data loss in long runs.

## Error Handling

The crawler includes basic handling for common runtime issues:

* **Download-triggered pages**
  Skipped when navigation results in file downloads rather than HTML content

* **Aborted requests (`net::ERR_ABORTED`)**
  Typically caused by non-standard resources or server-side blocking

* **Timeouts (15 seconds)**
  Prevents the crawler from hanging on slow or unresponsive pages

* **General exceptions**
  Logged and skipped to allow the crawler to continue processing

This ensures robustness in real-world web environments where failures are common.

---


