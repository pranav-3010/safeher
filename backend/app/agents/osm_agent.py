from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.agents.base_agent import DataSourceAgent
from app.models.spatial_features import OSMFeature, RoadSegment, EmergencyFacility
from app.services.data_processing import validate_coordinates, clean_text_string
from app.core.logging import logger

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class OSMAgent(DataSourceAgent):
    """
    Ingestion Agent for OpenStreetMap GIS data via Overpass API queries.
    Populates osm_features, road_segments (LineString), and emergency_facilities (Point) with PostGIS geometries.
    """

    def __init__(self, source_name: str = "OpenStreetMap India Overpass API"):
        super().__init__(source_name=source_name, source_type="osm")

    def fetch(self, bbox: Tuple[float, float, float, float] = (17.35, 78.45, 17.42, 78.52), timeout_sec: int = 20) -> List[Dict[str, Any]]:
        """
        Executes Overpass QL bounding-box query for amenities, facilities, and road ways.
        BBOX format: (min_lat, min_lng, max_lat, max_lng)
        """
        min_lat, min_lng, max_lat, max_lng = bbox
        query = f"""
        [out:json][timeout:15];
        (
          node["amenity"~"police|hospital|pharmacy|atm|bank|fuel|bus_station"]({min_lat},{min_lng},{max_lat},{max_lng});
          way["highway"~"primary|secondary|tertiary|residential"]({min_lat},{min_lng},{max_lat},{max_lng});
        );
        out body geom;
        """

        try:
            headers = {"User-Agent": "SafeHer-OSMBot/1.0 (+https://github.com/pranav-3010/safeher)"}
            res = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=timeout_sec)
            if res.status_code == 200:
                elements = res.json().get("elements", [])
                return elements
            logger.warning(f"Overpass API returned status: {res.status_code}")
            return []
        except Exception as e:
            logger.error(f"Overpass API fetch error: {e}")
            return []

    def validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Validates OSM record element type and geometry payload.
        """
        valid = []
        rejected = 0

        for r in raw_records:
            osm_type = r.get("type")
            osm_id = str(r.get("id")) if r.get("id") else None

            if not osm_type or not osm_id:
                rejected += 1
                continue

            tags = r.get("tags", {})
            name = clean_text_string(tags.get("name"))

            if osm_type == "node":
                lat, lng = r.get("lat"), r.get("lon")
                if not validate_coordinates(lat, lng):
                    rejected += 1
                    continue
                valid.append({
                    "element_type": "node",
                    "osm_id": f"node/{osm_id}",
                    "name": name,
                    "tags": tags,
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "geometry": None
                })

            elif osm_type == "way":
                geometry_pts = r.get("geometry", [])
                if len(geometry_pts) < 2:
                    rejected += 1
                    continue

                valid_pts = []
                for pt in geometry_pts:
                    lat, lng = pt.get("lat"), pt.get("lon")
                    if validate_coordinates(lat, lng):
                        valid_pts.append((lng, lat))

                if len(valid_pts) < 2:
                    rejected += 1
                    continue

                valid.append({
                    "element_type": "way",
                    "osm_id": f"way/{osm_id}",
                    "name": name,
                    "tags": tags,
                    "latitude": None,
                    "longitude": None,
                    "geometry_points": valid_pts
                })

        return valid, rejected

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Maps OSM tags to standardized facility categories and road types.
        """
        normalized = []
        for r in validated_records:
            tags = r.get("tags", {})
            r["retrieved_at"] = datetime.now(timezone.utc)

            if r["element_type"] == "node":
                amenity = tags.get("amenity", "other")
                if amenity in ["police", "hospital", "fuel", "bus_station"]:
                    facility_map = {
                        "police": "police",
                        "hospital": "hospital",
                        "fuel": "petrol_station",
                        "bus_station": "metro"
                    }
                    r["facility_type"] = facility_map.get(amenity, "other")
                else:
                    r["facility_type"] = None
                r["category"] = amenity

            elif r["element_type"] == "way":
                r["highway_type"] = tags.get("highway", "unclassified")
                r["oneway"] = True if tags.get("oneway") == "yes" else False if tags.get("oneway") == "no" else None
                r["max_speed"] = int(tags.get("maxspeed")) if tags.get("maxspeed") and tags.get("maxspeed").isdigit() else None
                r["lighting_status"] = tags.get("lit") if tags.get("lit") in ["yes", "no"] else None  # NULL = UNKNOWN

            normalized.append(r)
        return normalized

    def deduplicate(self, db: Session, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates OSM elements using osm_id against database.
        """
        osm_ids = [r["osm_id"] for r in normalized_records]
        if not osm_ids:
            return []

        existing_osm_ids = set(
            row[0] for row in db.query(OSMFeature.osm_id).filter(OSMFeature.osm_id.in_(osm_ids)).all()
        )

        return [r for r in normalized_records if r["osm_id"] not in existing_osm_ids]

    def store(self, db: Session, data_source_id: Any, records: List[Dict[str, Any]]) -> int:
        """
        Stores OSM features, emergency facilities (Points), and road segments (LineStrings) with PostGIS geometries.
        """
        if not records:
            return 0

        inserted_count = 0
        for r in records:
            # 1. Store in general osm_features table
            feature = OSMFeature(
                osm_id=r["osm_id"],
                feature_type=r["element_type"],
                name=r["name"],
                category=r.get("category", "infrastructure"),
                tags=r["tags"],
                source="OpenStreetMap",
                retrieved_at=r["retrieved_at"]
            )
            db.add(feature)
            db.flush()

            # 2. If Emergency Facility Node, populate emergency_facilities table
            if r["element_type"] == "node" and r.get("facility_type"):
                facility = EmergencyFacility(
                    name=r["name"] or f"OSM {r['facility_type'].title()} Facility",
                    facility_type=r["facility_type"],
                    source="OpenStreetMap",
                    source_reference=r["osm_id"],
                    verification_status="VERIFIED"
                )
                db.add(facility)
                db.flush()

                db.execute(text(
                    "UPDATE emergency_facilities SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
                ), {"lng": r["longitude"], "lat": r["latitude"], "id": facility.id})

            # 3. If Road Way, populate road_segments table with PostGIS LineString geometry & length
            elif r["element_type"] == "way":
                pts_str = ", ".join([f"{pt[0]} {pt[1]}" for pt in r["geometry_points"]])
                linestring_wkt = f"LINESTRING({pts_str})"

                segment = RoadSegment(
                    osm_id=r["osm_id"],
                    road_name=r["name"],
                    road_type=r.get("highway_type"),
                    max_speed=r.get("max_speed"),
                    oneway=r.get("oneway"),
                    lighting_status=r.get("lighting_status") # NULL = UNKNOWN (No fabrication!)
                )
                db.add(segment)
                db.flush()

                # Update LineString geometry & compute length in meters using ST_Length
                db.execute(text(
                    """
                    UPDATE road_segments 
                    SET geometry = ST_GeogFromText(:wkt),
                        length_meters = ST_Length(ST_GeogFromText(:wkt))
                    WHERE id = :id
                    """
                ), {"wkt": linestring_wkt, "id": segment.id})

            inserted_count += 1

        db.commit()
        return inserted_count
