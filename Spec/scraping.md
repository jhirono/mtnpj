# Design Specification: High-Performance Climbing Data Scraper

## 1. Overview

The goal is to build a new, high-performance scraper that aggregates climbing area and route information from Mountain Project. The output will be a structured JSON file that captures key details for each climbing area, its sub-areas, and routes. Unlike the legacy script, the new implementation will focus on speed and scalability by using concurrent requests and asynchronous I/O, while also supporting the extraction of additional data (e.g. user comments and statistics) that are only available to logged-in users.

## 2. Objectives

- **Performance:**  
  Significantly improve the scraping speed using asynchronous techniques (or concurrency) to process multiple pages in parallel.

- **Comprehensive Data Collection:**  
  Collect complete climbing data, including:
  - **Area Information:**  
    Capture data for top-level areas (e.g., “Castle Rock”) and nested sub-areas (e.g., “Upper Castle”)—recognizing that sub-areas fall under a parent area.
  - **Route Information:**  
    Extract route details for each sub-area. For example, a route under “Upper Castle.”
  - **Protected Data:**  
    Retrieve comments, statistics, and other metadata that are available only after login.

- **Maintainability & Extensibility:**  
  Write modular, well-documented code to make future enhancements (such as adding more fields or data sources) straightforward.

- **Robustness:**  
  Ensure error handling, retry logic, and logging so that transient failures or website changes do not derail the scraping process.

- **Authentication Support:**  
  Provide optional support for logging in so that login-restricted data (e.g. comments and stats) can be captured when desired.

## 3. Functional Requirements

- **Hierarchical Data Extraction:**
  - **Area vs. Sub-Area:**  
    Recognize and distinguish between a top-level area (e.g., “Castle Rock”) and its sub-areas (e.g., “Upper Castle”). The scraper should build the hierarchy so that routes are properly associated with the correct sub-area.
  - **Route Data:**  
    For each (sub-)area, extract route details including name, URL, grade, protection info, ratings, votes, first ascent (FA), description, location hints, and any available tags.
  
- **Authentication Handling:**
  - Support an optional login step so that pages displaying user comments, statistics, and additional metadata can be scraped.
  - Manage session cookies or tokens as required to access authenticated content.
  
- **Data Organization:**
  - Output a JSON file in which each climbing area is an object that includes its details, its hierarchy (with sub-areas nested or referenced), and an array of route objects.
  - Ensure that fields for comments and stats are captured when available.

- **Scraping Process:**
  - Use efficient, asynchronous HTTP requests to fetch pages concurrently.
  - Parse HTML using a robust parser to extract the required fields.
  - Handle any pagination or dynamic content if applicable.
  - Respect robots.txt and rate-limit requests to avoid overloading the source website.

## 4. Non-Functional Requirements

- **Speed & Scalability:**  
  The scraper should be designed to scale (handle hundreds of pages) without significant delays. Use asynchronous I/O (e.g., Python’s `asyncio` with `aiohttp`) or multi-threading/multiprocessing as appropriate.

- **Reliability:**  
  Incorporate robust error handling, automatic retries for transient network issues, and detailed logging for debugging purposes.

- **Modularity:**  
  The code should be divided into clearly defined modules, for example:
  - **HTTP Module:** Handles all network requests (with support for concurrency and authentication).
  - **Parser Module:** Extracts area, sub-area, and route data from HTML.
  - **Data Processor:** Organizes and cleans data into the required JSON schema.
  - **Authentication Module:** Implements the login flow and session management for accessing restricted content (comments, stats).

- **Configuration & Flexibility:**  
  Allow key parameters (such as concurrency limits, login credentials, timeouts, and user-agent strings) to be defined via configuration files or command-line arguments.

## 5. Data Model

- **Area Object:**
  - `area_id`
  - `area_url`
  - `area_name` (e.g., “Castle Rock”)
  - `area_gps`
  - `area_description`
  - `area_getting_there`
  - `area_tags`
  - `area_hierarchy` (an array or nested structure that defines the parent/child relationships; e.g., a top-level area and its sub-areas like “Upper Castle”)
  - `area_access_issues`
  - `area_page_views`
  - `area_shared_on`
  - `area_comments` *(if available – requires login)*
  - `routes` (array of associated route objects)

- **Route Object:**
  - `route_id`
  - `route_name`
  - `route_url`
  - `route_grade`
  - `route_protection_grading`
  - `route_stars`
  - `route_votes`
  - `route_type`
  - `route_pitches`
  - `route_lr`
  - `route_length_ft`
  - `route_length_meter`
  - `route_fa`
  - `route_description`
  - `route_location`
  - `route_protection`
  - `route_page_views`
  - `route_shared_on`
  - `route_tags`
  - `route_comments` *(if available – requires login)*
  - `route_suggested_ratings`
  - `route_tick_comments`
  - `route_stats` *(if available – requires login)*

## 6. Technical Approach

- **Asynchronous Fetching:**  
  Use asynchronous HTTP libraries (e.g., `aiohttp` with `asyncio`) to send concurrent requests. This will greatly reduce the total time needed for scraping.

- **HTML Parsing:**  
  Employ a robust HTML parser (such as BeautifulSoup or lxml) to extract data using CSS selectors or XPath expressions.

- **Authentication Handling:**  
  - Implement a mechanism to perform login (if credentials are provided) and store session cookies or tokens.
  - Use this authenticated session to request pages that include comments and statistics.
  
- **Error Handling & Logging:**  
  Implement try/except blocks with retry logic for network requests and parsing. Log all errors with sufficient context (e.g., URL, error message) to aid in debugging.

- **Output Generation:**  
  Serialize the aggregated data model into a JSON file once all pages have been processed.

## 7. Additional High-Level Design Directions

- **Hierarchy Management:**  
  Since the website distinguishes between areas (e.g., “Castle Rock”) and sub-areas (e.g., “Upper Castle”), the design should explicitly model and maintain these relationships. Cursor can decide whether to nest sub-areas within parent area objects or to reference them separately in the output.

- **Login & Session Management:**  
  Some data (like comments and route statistics) is only available after a user logs in. The design should allow:
  - Optional configuration for login credentials.
  - A session management mechanism that authenticates once and then reuses session cookies/tokens for subsequent requests.
  - Clear separation between public data and login-restricted data, with appropriate error handling if login fails.

- **Modular Implementation:**  
  Cursor is encouraged to select the most efficient libraries and architecture patterns that meet the above requirements while remaining flexible. The implementation details (e.g., whether to use a headless browser for login or direct HTTP POST requests) can be decided based on current best practices and available libraries.

## 8. Expected Outcome

The final deliverable will be a fast, robust, and modular Python-based scraper that:
- Retrieves climbing area and route data efficiently from Mountain Project.
- Properly distinguishes between top-level areas and sub-areas, associating routes with the correct hierarchical level.
- Captures both public data and, when configured, login-restricted data (comments and statistics).
- Outputs a well-structured JSON file that can be used for further analysis or as the backend for a climbing route search service.