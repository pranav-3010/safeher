# Supabase PostGIS Geospatial Architecture & Indexing (Phase 2)

## 📌 PostGIS Overview
PostGIS enables **PostgreSQL** to handle spatial data types (`GEOGRAPHY` and `GEOMETRY`), calculate real-world distances in meters, check intersection of route polylines with danger zones, and perform high-performance spatial indexing using **GiST (Generalized Search Tree)** indexes.

---

## 🗺️ Geography vs. Geometry Types

In `SafeHer`, we use `GEOGRAPHY(..., 4326)` (WGS 84 spatial reference) for all real-world coordinates:

* **`GEOGRAPHY(Point, 4326)`:** Used for point coordinates (e.g. incidents, facilities, SOS alerts, start/end points). Distance calculations (`ST_Distance`, `ST_DWithin`) are computed in **real-world meters** automatically on the ellipsoid surface without projection distortion.
* **`GEOGRAPHY(LineString, 4326)`:** Used for `road_segments` geometries to measure exact road length in meters and calculate spatial intersection with risk buffer zones.
* **`GEOGRAPHY(Geometry, 4326)`:** Used for generic OpenStreetMap features (`osm_features`) supporting Points, LineStrings, and Polygons.

---

## ⚡ GiST Spatial Indexing Strategy

Spatial queries without indexes require expensive full table scans. `SafeHer` creates **GiST indexes** on all spatial columns:

```sql
-- Spatial GiST Indexes created in Alembic Migration 001:
CREATE INDEX idx_crime_incidents_location ON crime_incidents USING gist (location);
CREATE INDEX idx_news_incidents_location ON news_incidents USING gist (location);
CREATE INDEX idx_community_reports_location ON community_reports USING gist (location);
CREATE INDEX idx_osm_features_geometry ON osm_features USING gist (geometry);
CREATE INDEX idx_road_segments_geometry ON road_segments USING gist (geometry);
CREATE INDEX idx_emergency_facilities_location ON emergency_facilities USING gist (location);
CREATE INDEX idx_risk_events_location ON risk_events USING gist (location);
CREATE INDEX idx_route_analyses_source_location ON route_analyses USING gist (source_location);
CREATE INDEX idx_route_analyses_dest_location ON route_analyses USING gist (destination_location);
CREATE INDEX idx_emergency_events_location ON emergency_events USING gist (location);
```

---

## 🔍 Core PostGIS Spatial Queries Used in Backend

### 1. Nearby Emergency Facilities Search (Within 1 km)
Finds all verified emergency safe havens within `1000` meters of user position `(17.3850, 78.4867)`:

```sql
SELECT 
    name, 
    facility_type, 
    ST_Distance(location, ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326)) AS distance_meters
FROM emergency_facilities
WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326), 1000)
ORDER BY distance_meters ASC;
```

### 2. Active Risk Events Near Road Segment (Within 500 meters)
Finds active risk events near a road segment:

```sql
SELECT 
    e.event_type, 
    e.severity, 
    ST_Distance(e.location, r.geometry) AS distance_meters
FROM risk_events e
JOIN road_segments r ON r.id = 'YOUR-ROAD-UUID'
WHERE ST_DWithin(e.location, r.geometry, 500)
  AND e.valid_from <= NOW() 
  AND (e.valid_until IS NULL OR e.valid_until >= NOW());
```

### 3. Nearest Road Segment Match to Coordinates
Finds nearest road segment for snapping coordinates:

```sql
SELECT 
    id, 
    road_name, 
    road_type,
    ST_Distance(geometry, ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326)) AS distance_meters
FROM road_segments
WHERE ST_DWithin(geometry, ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326), 100)
ORDER BY distance_meters ASC
LIMIT 1;
```

---

## 🚀 PostGIS Verification Command
To verify PostGIS is running in your Supabase PostgreSQL instance:

```sql
SELECT PostGIS_Version();
```
*Expected Output:* `3.4.0 USE_GEOS=1 USE_PROJ=1 USE_STATS=1`
