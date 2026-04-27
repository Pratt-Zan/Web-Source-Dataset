# Web-Source-Dataset
This project is for the code structure for monthly update of the source in Public companies' page source in text. The structure for the whole code can be seperated into **2 parts: THE ITER SEARCH / THE SITEMAP**. In words, the iter search is from the idea that we can find each url in multiple layers and scrap them in order, and the deeper the more. While sitemap can give you a direct set of urls in advance, which will also update daily. Both methods have advantages, Iter Search is **available in all cases but is not sufficient, and slower**, while sitemap is very **full but may not work in certain domains** (it is very reliable but just not 100%) . For database construction I recommend using sitemap first, and adjust for the second round.

Here below I will show the details of 2 methods and start with ITER SEARCH.

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

# 🌐 Part-1: Sitemap-Based URL Discovery with Incremental Updates

## Overview

This module implements a **sitemap-driven URL discovery system** designed to efficiently extract **all accessible page URLs** from company websites. Unlike traditional crawlers that rely on link traversal, this approach leverages **XML sitemaps** to obtain a more complete and structured view of a website’s content.

The system is particularly useful as a **preprocessing stage** for large-scale web data pipelines, where the goal is to:

* Build a **comprehensive URL universe** for each company
* Track **newly added pages over time**
* Enable downstream tasks such as **text crawling, NLP, or financial disclosure analysis**

To ensure efficiency across repeated runs, the system incorporates an **incremental update mechanism**, allowing it to:

* Compare newly discovered URLs with historical records
* Store only **previously unseen URLs**
* Maintain a continuously updated **full URL database**

## Key Features

This module is designed for **completeness, efficiency, and robustness** in URL collection:

* **Sitemap-Based Crawling (High Coverage)**
  Instead of relying on in-page links, the system extracts URLs directly from:

  * `robots.txt` declarations
  * XML sitemap files
    This ensures significantly higher coverage, especially for large or deeply nested websites.

* **Recursive Sitemap Parsing**
  Supports **nested sitemap structures** (`sitemap index` files), recursively traversing:

  * `<sitemap>` entries (child sitemaps)
  * `<url>` entries (actual page URLs)

* **Incremental URL Tracking**
  Maintains:

  * A **full historical URL database**
  * A **run-specific incremental update file**
    Only newly discovered URLs are recorded in each run.

* **Efficient Deduplication via Set Operations**
  Uses Python `set` structures to:

  * Remove duplicates efficiently
  * Compute differences between current and historical data

* **Custom User-Agent Support**
  Mimics a real browser request to reduce the likelihood of request blocking.

* **Memory-Aware Design**
  Pages are opened and closed per site to avoid memory accumulation during large-scale crawling.

## Project Structure

```id="2j7c2r"
project/
│
├── Company.json
│   Input file containing company names and base URLs
│
├── json_sitemap/
│   ├── Company_all_urls_sitemap_full.json
│   │   Full historical URL database
│   │
│   └── url_update/
│       └── Company_new_urls_YYYYMMDD.json
│           Incremental file storing newly discovered URLs
│
└── sitemap_crawler.py
    Main script for sitemap parsing and URL extraction
```

This structure separates:

* **Input configuration**
* **Persistent historical data**
* **Incremental updates for each run**

## Input Data Format

### `Company.json`

Same structure as the main crawler:

```json id="ydg8dy"
[
    {
        "name": "CompanyA",
        "url": "https://www.companya.com"
    }
]
```

### Input Requirements

* The `url` should represent the **base domain** of the company
* The system assumes the sitemap is located via:

  * `robots.txt`, or
  * default path `/sitemap.xml`

## Output Data Format

### 1. Full URL Database

**File:** `Company_all_urls_sitemap_full.json`

This file stores the **complete set of known URLs** for each company.

```json id="sdb7h3"
{
    "CompanyA": [
        "https://www.companya.com/page1",
        "https://www.companya.com/page2"
    ]
}
```

Key characteristics:

* URLs are stored as **lists** (converted from sets before saving)
* Continuously updated after each run
* Serves as the **baseline for detecting new URLs**

### 2. Incremental URL File

**File:** `Company_new_urls_YYYYMMDD.json`

Contains only **newly discovered URLs** during the current execution.

```json id="4v9b4q"
{
    "CompanyA": [
        "https://www.companya.com/new-page"
    ]
}
```

Key characteristics:

* Generated dynamically using the current date
* Only includes **new URLs not seen in previous runs**
* Empty results are not saved

## Installation

### Requirements

* Python 3.8+
* Playwright
* BeautifulSoup (for XML parsing)

### Install Dependencies

```bash id="b0y2i8"
pip install playwright beautifulsoup4
playwright install
```

## Usage

### Step 1: Configure File Paths

Modify the following variables in `main()`:

```python id="k0kq7h"
input_json_file = 'path/to/Company.json'
output_json_file = 'path/to/Company_all_urls_sitemap_full.json'
new_urls_output_file = 'path/to/url_update/Company_new_urls_YYYYMMDD.json'
```

### Step 2: Run the Script

```bash id="n6h8c1"
python sitemap_crawler.py
```

Execution workflow:

1. Load company list
2. Load historical URL database (if exists)
3. Discover sitemap locations
4. Extract all URLs recursively
5. Compare with historical data
6. Save full and incremental results

## Crawling Logic

### Step 1: Discover Sitemap URLs

The system first attempts to retrieve sitemap locations from:

```
https://example.com/robots.txt
```

It scans for lines starting with:

```
Sitemap: https://example.com/sitemap.xml
```

If no sitemap is declared, it falls back to:

```
https://example.com/sitemap.xml
```

### Step 2: Recursive Sitemap Parsing

Each sitemap is parsed as XML using BeautifulSoup:

* `<sitemap>` tags → indicate nested sitemap files
* `<url>` tags → contain actual webpage URLs

The function recursively processes all nested sitemaps until all URLs are collected.

### Step 3: URL Aggregation

For each site:

* All extracted URLs are stored in a **temporary set**
* This ensures automatic deduplication within the current run

### Step 4: Incremental Comparison

New URLs are identified using set difference:

```python id="vtx3l2"
newly_discovered_urls = current_scraped_urls - existing_urls
```

This operation ensures:

* Only unseen URLs are recorded
* Historical database remains clean and non-redundant

### Step 5: Database Update

* Full database is updated with new URLs
* Incremental file is created only if new URLs are found

## Performance Optimizations

* **Set-Based Deduplication**
  Efficient handling of large URL volumes

* **Single Browser Context**
  Reuses the same browser session to reduce overhead

* **Controlled Page Lifecycle**
  Each page is explicitly closed after processing to free memory

* **Timeout Control (20s)**
  Prevents hanging on slow or invalid sitemap URLs

* **User-Agent Spoofing**
  Reduces the likelihood of request blocking by servers

## Error Handling

The system is designed to handle common real-world issues:

* **robots.txt access failure**
  Falls back to default sitemap location

* **Invalid or unreachable sitemap URLs**
  Skips and continues processing

* **Malformed XML content**
  Handled via exception catching

* **Network timeouts**
  Prevents blocking execution

* **Site-level failure isolation**
  Errors in one site do not affect others

  Here is the **third module README (Text Extraction Layer)**, written in the same detailed, consistent style as the previous two. This one fits as the **final stage in your pipeline (URL → Text)**.

---

# 🌐 Part-2: Web Text Extraction with Incremental Storage

## Overview

This module implements a **high-performance text extraction engine** that converts a pre-collected set of URLs into a structured **plain-text database**. It is designed as the **final stage of a multi-step web data pipeline**, where:

1. URLs are first discovered (e.g., via sitemap crawling)
2. Then processed here to extract **human-readable textual content**

The system emphasizes **speed, scalability, and incremental updates**, making it suitable for large-scale data collection tasks such as:

* Corporate disclosure analysis
* ESG / sustainability text mining
* Financial communication research
* Longitudinal website monitoring

A key design goal is to avoid redundant work. Therefore, the system maintains a **persistent historical text database**, allowing it to:

* Skip already processed URLs in **O(1) time**
* Only extract text from **previously unseen pages**
* Generate a **monthly (or periodic) incremental dataset**

## Key Features

This module is optimized for **fast and repeatable large-scale text extraction**:

* **Ultra-Fast DOM-Based Text Extraction**
  Uses:

  ```javascript
  document.body.innerText
  ```

  to directly retrieve **visible page content**, avoiding costly HTML parsing.

* **Incremental Processing Framework**
  Each run:

  * Loads historical text data
  * Skips known URLs instantly
  * Stores only newly extracted content

* **Playwright-Based Asynchronous Engine**
  Ensures efficient handling of large URL volumes with minimal blocking.

* **Global Resource Blocking**
  Improves performance by disabling:

  * Images
  * CSS
  * Fonts
  * Media

* **Per-Site Processing Isolation**
  Each site is processed in a dedicated browser page to:

  * Improve stability
  * Avoid cross-site interference
  * Enable controlled memory usage

* **Automatic Progress Persistence**
  Saves the full database after each site to prevent data loss in long-running jobs

## Project Structure

```id="wq9c1l"
project/
│
├── json_sitemap/
│   └── Company_all_urls_sitemap_full.json
│       Input: full list of URLs collected from sitemap crawler
│
├── text_sitemap/
│   ├── Company_text_full.json
│   │   Full historical text database
│   │
│   └── text_update/
│       └── Company_new_text_YYYYMMDD.json
│           Incremental text output for current run
│
└── text_extractor.py
    Main script for high-speed text extraction
```

This module assumes that the **URL discovery stage has already been completed**.

## Input Data Format

### URL Source File

**File:** `Company_all_urls_sitemap_full.json`

```json id="7g6m4m"
{
    "CompanyA": [
        "https://www.companya.com/page1",
        "https://www.companya.com/page2"
    ]
}
```

### Input Characteristics

* Organized by **site name**
* Each site contains a list of URLs
* URLs are assumed to be **deduplicated beforehand**

## Output Data Format

### 1. Full Text Database

**File:** `Company_text_full.json`

This file stores all extracted textual content:

```json id="qk1h1h"
{
    "CompanyA": {
        "https://www.companya.com/page1": "Extracted visible text...",
        "https://www.companya.com/page2": "Extracted visible text..."
    }
}
```

Key design choices:

* Dictionary structure enables **O(1) lookup**
* Each URL maps directly to its **full text content**
* Used as the **reference for skipping processed pages**

### 2. Incremental Text File

**File:** `Company_new_text_YYYYMMDD.json`

Contains only newly extracted pages:

```json id="k2h6hp"
{
    "CompanyA": {
        "https://www.companya.com/new-page": "Extracted text..."
    }
}
```

Key characteristics:

* Generated per execution
* Only includes **previously unseen URLs**
* Can be used for **delta analysis or model updates**

## Installation

### Requirements

* Python 3.8+
* Playwright

### Install Dependencies

```bash id="zz1o3r"
pip install playwright
playwright install
```

## Usage

### Step 1: Configure File Paths

Modify the following variables in `main()`:

```python id="lcf6og"
input_urls_file = 'path/to/Company_all_urls_sitemap_full.json'
output_text_full = 'path/to/Company_text_full.json'
output_text_new = 'path/to/text_update/Company_new_text_YYYYMMDD.json'
```

### Step 2: Run the Script

```bash id="x7h4wt"
python text_extractor.py
```

Execution workflow:

1. Load full URL dataset
2. Load historical text database (if exists)
3. Iterate through each site
4. Skip already processed URLs
5. Extract text from new pages
6. Update both full and incremental outputs

## Crawling & Extraction Logic

### Step 1: URL Iteration

For each site:

* Loop through all URLs
* Check existence in historical database

```python id="1q7u8w"
if url in historical_text_data[site_name]:
    continue
```

This ensures **constant-time skipping** of known pages.

### Step 2: Page Fetching

Pages are loaded using:

```python id="v9t9lm"
await page.goto(url, wait_until="domcontentloaded", timeout=15000)
```

This strategy:

* Avoids full page load overhead
* Is sufficient for extracting DOM text

### Step 3: Text Extraction

Core extraction logic:

```javascript id="m4kz7n"
document.body.innerText.trim()
```

Advantages:

* Captures **only visible text**
* Automatically removes:

  * HTML tags
  * Scripts
  * Styles

This produces clean input for downstream NLP tasks.

### Step 4: Incremental Update Logic

New content is stored in both:

* Full database:

```python id="2znxvk"
historical_text_data[site_name][url] = page_text
```

* Incremental dataset:

```python id="2c2tql"
new_text_results[site_name][url] = page_text
```

### Step 5: Rate Control

A delay is added:

```python id="6t5z7g"
await asyncio.sleep(0.5)
```

This helps:

* Prevent server overload
* Reduce risk of IP blocking

## Performance Optimizations

* **Global Resource Blocking**

  ```python
  route.abort() if resource_type in ["image", "stylesheet", "media", "font"]
  ```

  Significantly reduces load time

* **Single Page per Site**
  Minimizes browser overhead while maintaining isolation

* **Incremental Skipping**
  Avoids re-fetching already processed URLs entirely

* **Frequent Disk Writes**
  Prevents total data loss in long-running processes

* **Lightweight DOM Extraction**
  Avoids expensive parsing libraries like BeautifulSoup

## Error Handling

The system accounts for common runtime issues:

* **Non-200 Responses**
  Skipped immediately

* **Download-triggered URLs**
  Identified and ignored

* **Aborted Requests**
  Typically non-HTML content or blocked resources

* **Timeouts (15s)**
  Prevent execution stalls

* **Site-Level Isolation**
  Errors in one site do not interrupt others
