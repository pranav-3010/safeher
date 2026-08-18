# Supabase PostgreSQL Database Schema Specification (Phase 2)

## 📌 Architectural Overview
The **Women Safety Risk-Zone Prediction System (`SafeHer`)** database is hosted on **Supabase PostgreSQL** with **PostGIS** geospatial capabilities. The schema contains **17 core tables** designed for scalable spatial querying, historical data tracking, machine learning predictions, and secure row-level access control.

---

## 🗺️ Entity Relationship Overview

```
                      ┌───────────────────┐
                      │   data_sources    │
                      └─────────┬─────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
  source_fetches         crime_incidents        news_articles
                                                      │
                                                      ▼
                                                news_incidents

  ┌───────────────────┐               ┌───────────────────┐
  │   road_segments   │               │   model_versions  │
  └─────────┬─────────┘               └─────────┬─────────┘
            │                                   │
      ┌─────┴─────┐                       ┌─────┴─────┐
      ▼           ▼                       ▼           ▼
environmental_   risk_predictions ◄───────┴─── model_predictions
   features

  ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
  │emergency_facilities│   │ community_reports │   │   risk_events     │
  └───────────────────┘   └───────────────────┘   └───────────────────┘
```

---

## 🗄️ Detailed Table Specifications

### 1. `data_sources`
* **Purpose:** Registry for external and internal data providers (government, police, OSM, news).
* **Fields:** `id` (UUID), `name`, `organization`, `source_type`, `official_url`, `description`, `geographic_coverage`, `license`, `terms_of_use`, `access_method`, `update_frequency`, `historical_start_date`, `historical_end_date`, `geographic_precision`, `is_active`, `is_verified`, `created_at`, `updated_at`.

### 2. `source_fetches`
* **Purpose:** Ingestion run execution logs for monitoring data pipeline reliability.
* **Fields:** `id` (UUID), `data_source_id` (FK ➔ `data_sources.id`), `started_at`, `completed_at`, `status`, `records_fetched`, `records_inserted`, `records_updated`, `records_rejected`, `error_message`, `metadata_json`, `created_at`.

### 3. `crime_incidents`
* **Purpose:** Official verified and reported crime incident data.
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `external_source_id`, `data_source_id` (FK), `incident_type`, `description`, `reported_at`, `occurred_at`, `latitude`, `longitude`, `location`, `severity` (0.0-1.0), `source_confidence` (0.0-1.0), `verification_status`, `source_reference`, `raw_data`, `created_at`, `updated_at`.

### 4. `news_articles`
* **Purpose:** Ingested news media articles referencing safety and local incidents.
* **Fields:** `id`, `data_source_id` (FK), `external_article_id`, `title`, `description`, `content_reference`, `url`, `publisher`, `published_at`, `retrieved_at`, `language`, `content_hash` (UNIQUE), `processing_status`, `llm_processed`, `created_at`, `updated_at`.

### 5. `news_incidents`
* **Purpose:** Structured incident events extracted from news articles by LLM NLP agents.
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `news_article_id` (FK), `event_type`, `location_text`, `location`, `occurred_at`, `severity`, `llm_confidence`, `verification_status`, `extraction_metadata`, `valid_from`, `valid_until`, `created_at`, `updated_at`.

### 6. `community_reports`
* **Purpose:** User-submitted crowdsourced safety reports (prepared for Supabase RLS).
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `user_reference`, `report_type`, `description`, `location`, `reported_at`, `occurred_at`, `verification_status`, `confidence`, `review_status`, `created_at`, `updated_at`.

### 7. `osm_features`
* **Purpose:** Points of interest, amenities, and geographical facilities from OpenStreetMap.
* **Spatial Columns:** `location` (`GEOGRAPHY(Point, 4326)`), `geometry` (`GEOGRAPHY(Geometry, 4326)` with **GiST Index**).
* **Fields:** `id`, `osm_id`, `feature_type`, `name`, `category`, `location`, `geometry`, `tags`, `source`, `retrieved_at`, `created_at`, `updated_at`.

### 8. `road_segments`
* **Purpose:** Primary road polyline network connected to OSRM and ML risk engines.
* **Spatial Column:** `geometry` (`GEOGRAPHY(LineString, 4326)` with **GiST Index**).
* **Fields:** `id`, `osm_id`, `road_name`, `road_type`, `geometry`, `length_meters`, `max_speed`, `oneway`, `has_sidewalk`, `is_dead_end`, `intersection_density`, `lighting_status`, `commercial_activity_score`, `created_at`, `updated_at`.

### 9. `emergency_facilities`
* **Purpose:** Safe haven shelters (Police, Hospitals, Metro, Petrol Pumps, Fire Stations).
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `name`, `facility_type`, `location`, `address`, `phone`, `is_24_hours`, `source`, `source_reference`, `verification_status`, `last_verified_at`, `created_at`, `updated_at`.

### 10. `environmental_features`
* **Purpose:** Physical street lighting, foot traffic, and road width features bound to road segments.
* **Fields:** `id`, `road_segment_id` (FK ➔ `road_segments.id`), `lighting_status`, `lighting_source`, `commercial_activity`, `foot_traffic_indicator`, `visibility_indicator`, `road_width`, `footpath_available`, `surveillance_indicator`, `confidence`, `source_reference`, `observed_at`, `created_at`, `updated_at`.

### 11. `risk_events`
* **Purpose:** Unified real-time risk events (crime, harassment, unlit road, protests, events).
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `event_type`, `source_type`, `source_reference`, `description`, `location`, `severity` (0.0-1.0), `confidence` (0.0-1.0), `verification_status`, `valid_from`, `valid_until`, `created_at`, `updated_at`.

### 12. `model_versions`
* **Purpose:** Machine learning registry tracking versions, algorithm, feature list, and metrics.
* **Fields:** `id`, `model_name`, `version` (UNIQUE), `algorithm`, `training_started_at`, `training_completed_at`, `training_data_start`, `training_data_end`, `feature_list`, `metrics`, `artifact_uri`, `status`, `created_at`.

### 13. `risk_predictions`
* **Purpose:** Final dynamic risk predictions for road segments.
* **Fields:** `id`, `road_segment_id` (FK), `prediction_time`, `time_of_day`, `day_of_week`, `risk_score` (0.0-1.0), `confidence` (0.0-1.0), `risk_level` (LOW, MODERATE, HIGH, UNKNOWN), `model_version_id` (FK), `data_freshness`, `feature_snapshot`, `created_at`, `updated_at`.

### 14. `model_predictions`
* **Purpose:** Raw ML model output predictions recorded before risk fusion.
* **Fields:** `id`, `model_version_id` (FK), `road_segment_id` (FK), `prediction_time`, `prediction`, `confidence`, `features`, `created_at`.

### 15. `route_analyses`
* **Purpose:** Audit log of route evaluation requests, safety costs, and risk statistics.
* **Spatial Columns:** `source_location` (`GEOGRAPHY(Point, 4326)`), `destination_location` (`GEOGRAPHY(Point, 4326)`).
* **Fields:** `id`, `request_id`, `source_location`, `destination_location`, `requested_at`, `departure_time`, `route_provider`, `route_count`, `selected_route`, `safety_cost`, `distance_meters`, `duration_seconds`, `average_risk`, `maximum_risk`, `high_risk_percentage`, `confidence`, `metadata_json`, `created_at`.

### 16. `emergency_events`
* **Purpose:** Emergency SOS alerts (manual, voice, shake) prepared for Supabase RLS.
* **Spatial Column:** `location` (`GEOGRAPHY(Point, 4326)` with **GiST Index**).
* **Fields:** `id`, `event_reference` (UNIQUE), `user_reference`, `location`, `trigger_type`, `triggered_at`, `status`, `notification_status`, `notification_provider`, `resolved_at`, `metadata_json`, `created_at`, `updated_at`.

### 17. `system_logs`
* **Purpose:** System event and error logs excluding sensitive credentials.
* **Fields:** `id`, `service`, `level`, `event_type`, `message`, `source_reference`, `metadata_json`, `created_at`.

---

## 🔒 Supabase Security & Row Level Security (RLS) Strategy

* **Public Tables (Read-Only to Frontend):** `emergency_facilities`, `road_segments`, `risk_predictions`.
* **Authenticated User Tables (RLS Enabled):** `community_reports`, `emergency_events` (Users can insert and view their own reports).
* **Backend-Only Admin Tables:** `data_sources`, `source_fetches`, `model_versions`, `model_predictions`, `system_logs` (Restricted to Server-side Service Role).
