# Verified Real-World Data Sources Specification (Phase 3)

## 📌 Registered Data Providers

### 1. OpenStreetMap Overpass API (`osm-overpass-india`)
* **Organization:** OpenStreetMap Foundation
* **Access Method:** Overpass QL POST requests to `https://overpass-api.de/api/interpreter`
* **Data Ingested:** Roads (`LineString`), Police Stations (`Point`), Hospitals (`Point`), Metro Stations (`Point`), Petrol Pumps (`Point`), ATMs (`Point`).
* **License & Terms:** ODbL (Open Database License). Complies with rate limiting (max 2 queries per second, user-agent identified).
* **Geographic Precision:** Exact PostGIS Geography coordinates (`EPSG:4326`).

### 2. Google News RSS Safety Feed (`google-news-rss-safety`)
* **Organization:** Public News RSS Aggregator
* **Access Method:** Public XML RSS Fetching (`https://news.google.com/rss/search?q=women+safety+india&hl=en-IN`)
* **Data Ingested:** Article Title, Publisher, URL, Published Date, Content Hash. Full text is NOT stored.
* **License & Terms:** Standard Public RSS Consumption.
* **Geographic Precision:** Preserved as raw `location_text` until verified.

### 3. NCRB Open Crime Data Portal (`ncrb-open-data`)
* **Organization:** National Crime Records Bureau (NCRB) India
* **Access Method:** `data.gov.in` Open Data API / Open CSV Download
* **Data Ingested:** State and District level crime statistics.
* **License & Terms:** Government Open Data License (GODL) India.
* **Geographic Precision:** District Level Granularity (Preserved as District boundaries without inventing fake lat/long point coordinates).
