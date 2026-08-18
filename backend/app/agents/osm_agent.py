import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.agents.base_agent import DataSourceAgent
from app.models.spatial_features import OSMFeature, RoadSegment, EmergencyFacility
from app.services.data_processing import validate_coordinates, clean_text_string
from app.core.logging import logger

OSM_API_URL = "https://api.openstreetmap.org/api/0.6/map"


class OSMAgent(DataSourceAgent):
    """
    Ingestion Agent for OpenStreetMap GIS data via Official OpenStreetMap v0.6 API.
    Populates osm_features, road_segments (LineString), and emergency_facilities (Point) with PostGIS geometries.
    """

    def __init__(self, source_name: str = "OpenStreetMap India API"):
        super().__init__(source_name=source_name, source_type="osm")

    def fetch(self, bbox: Tuple[float, float, float, float] = (17.38, 78.47, 17.40, 78.49), timeout_sec: int = 25) -> List[Dict[str, Any]]:
        """
        Fetches map features from official OpenStreetMap v0.6 API for target bounding box.
        BBOX format for OSM v0.6 API: (min_lng, min_lat, max_lng, max_lat)
        """
        min_lat, min_lng, max_lat, max_lng = bbox
        url = f"{OSM_API_URL}?bbox={min_lng},{min_lat},{max_lng},{max_lat}"
        headers = {"User-Agent": "SafeHer-OSMBot/1.0 (+https://github.com/pranav-3010/safeher)"}

        try:
            res = requests.get(url, headers=headers, timeout=timeout_sec)
            if res.status_code != 200:
                logger.warning(f"OSM API returned HTTP status: {res.status_code}")
                return []

            root = ET.fromstring(res.content)
            
            # Map node ID -> (lat, lng)
            node_coords = {}
            elements = []

            # 1. Parse Nodes
            for node in root.findall("node"):
                node_id = node.get("id")
                lat = float(node.get("lat"))
                lng = float(node.get("lon"))
                node_coords[node_id] = (lat, lng)

                tags = {tag.get("k"): tag.get("v") for tag in node.findall("tag")}
                amenity = tags.get("amenity")
                if amenity or tags.get("name"):
                    elements.append({
                        "type": "node",
                        "id": node_id,
                        "lat": lat,
                        "lon": lng,
                        "tags": tags
                    })

            # 2. Parse Ways (Roads)
            for way in root.findall("way"):
                way_id = way.get("id")
                tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
                highway = tags.get("highway")

                if highway:
                    pts = []
                    for nd in way.findall("nd"):
                        ref = nd.get("ref")
                        if ref in node_coords:
                            pts.append({"lat": node_coords[ref][0], "lon": node_coords[ref][1]})

                    if len(pts) >= 2:
                        elements.append({
                            "type": "way",
                            "id": way_id,
                            "tags": tags,
                            "geometry": pts
                        })

            logger.info(f"Successfully fetched {len(elements)} relevant OSM elements from Official OSM API.")
            return elements

        except Exception as e:
            logger.error(f"Failed to fetch from OpenStreetMap API: {e}")
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
                facility_map = {
                    "police": "police",
                    "hospital": "hospital",
                    "fuel": "petrol_station",
                    "bus_station": "metro",
                    "pharmacy": "hospital"
                }
                r["facility_type"] = facility_map.get(amenity)
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

            # 2. If Emergency Facility Node, populate emergency_facilities table
            if r["element_type"] == "node" and r.get("facility_type"):
                facility = EmergencyFacility(
                    name=r["name"] or f"OSM {r['facility_type'].title()} Facility",
                    facility_type=r["facility_type"],
                    location=func.ST_SetSRID(func.ST_MakePoint(r["longitude"], r["latitude"]), 4326),
                    source="OpenStreetMap",
                    source_reference=r["osm_id"],
                    verification_status="VERIFIED"
                )
                db.add(facility)

            # 3. If Road Way, populate road_segments table with PostGIS LineString geometry
            elif r["element_type"] == "way":
                pts_str = ", ".join([f"{pt[0]} {pt[1]}" for pt in r["geometry_points"]])
                linestring_wkt = f"LINESTRING({pts_str})"

                segment = RoadSegment(
                    osm_id=r["osm_id"],
                    road_name=r["name"],
                    road_type=r.get("highway_type"),
                    geometry=func.ST_GeogFromText(linestring_wkt),
                    length_meters=0.0,
                    max_speed=r.get("max_speed"),
                    oneway=r.get("oneway"),
                    lighting_status=r.get("lighting_status") # NULL = UNKNOWN (No fabrication!)
                )
                db.add(segment)

            inserted_count += 1

        db.commit()

        # Update PostGIS length_meters on inserted road segments using ST_Length
        db.execute(text("UPDATE road_segments SET length_meters = ST_Length(geometry) WHERE length_meters = 0.0 OR length_meters IS NULL"))
        db.commit()

        return inserted_count
