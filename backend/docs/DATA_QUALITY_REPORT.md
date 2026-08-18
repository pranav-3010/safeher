# Real-World Data Quality & Provenance Report (Phase 3)

**Report Generated At (UTC):** `2026-08-18T06:49:33.598518+00:00`

---

## 📊 Ingestion Pipeline Summary
* **Registered Data Sources:** `3`
* **Total Fetch Execution Runs:** `0`
* **Successful Fetches:** `0`

---

## 🗄️ Database Record Statistics

| Database Table | Record Count | Geographic Coordinates Status |
| :--- | :--- | :--- |
| **`crime_incidents`** | `0` | `0` verified coordinates, `0` missing/district-level |
| **`news_articles`** | `0` | Deduplicated via SHA-256 content hashes |
| **`osm_features`** | `0` | Real OSM POIs & amenity geometries |
| **`road_segments`** | `0` | PostGIS `LineString` network polylines |
| **`emergency_facilities`** | `0` | PostGIS `Point` geography safe havens |
| **`community_reports`** | `0` | Unverified crowdsourced user reports |

---

## 🛡️ Data Provenance & Quality Standards
1. **No Synthetic Data:** Zero synthetic crime or fabricated records were generated.
2. **Missing Coordinates Preserved:** District/state-level statistics keep coordinates `NULL` rather than fabricating fake point locations.
3. **Deduplication Strategy:** News articles use SHA-256 `content_hash + publisher`; OSM data uses `osm_id`.
