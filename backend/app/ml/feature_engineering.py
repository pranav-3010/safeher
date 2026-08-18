import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
from app.services.geographic_engine import GeographicEngine

FEATURE_NAMES = [
    "latitude",
    "longitude",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "month",
    "incidents_within_radius",
    "nearest_police_distance",
    "nearest_hospital_distance",
    "spatial_density"
]

class FeatureEngineeringPipeline:
    """
    Feature Engineering Pipeline for Phase 6 Historical ML Model.
    Transforms raw latitude, longitude, and timestamp observations into numerical feature matrices.
    """

    @staticmethod
    def extract_features(
        db: Session,
        latitude: float,
        longitude: float,
        timestamp: datetime,
        radius_meters: float = 2000.0
    ) -> List[float]:
        """
        Extracts temporal and spatial features for a single location and time observation.
        """
        hour_of_day = timestamp.hour
        day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
        is_weekend = 1.0 if day_of_week in [5, 6] else 0.0
        month = timestamp.month

        # PostGIS Spatial Queries
        incidents_data = GeographicEngine.get_nearby_incidents(
            db, lat=latitude, lng=longitude, radius_meters=radius_meters, limit=50
        )
        incidents_count = float(incidents_data.get("count", 0))

        police_facility = GeographicEngine.get_nearest_facility(
            db, lat=latitude, lng=longitude, facility_type="police"
        )
        police_dist = float(police_facility["distance_meters"]) if police_facility else 1080.0

        hospital_facility = GeographicEngine.get_nearest_facility(
            db, lat=latitude, lng=longitude, facility_type="hospital"
        )
        hospital_dist = float(hospital_facility["distance_meters"]) if hospital_facility else 355.0

        density_data = GeographicEngine.get_crime_density_and_signals(
            db, lat=latitude, lng=longitude, radius_meters=radius_meters
        )
        density = float(density_data.get("spatial_crime_density_per_sq_km", 0.32))

        return [
            float(latitude),
            float(longitude),
            float(hour_of_day),
            float(day_of_week),
            is_weekend,
            float(month),
            incidents_count,
            police_dist,
            hospital_dist,
            density
        ]

    @staticmethod
    def build_feature_matrix(
        db: Session,
        dataset: List[Dict[str, Any]],
        radius_meters: float = 2000.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Builds feature matrix X and target labels y from valid historical dataset.
        Target: 1 if severity >= 0.7 or incidents > 0, else 0.
        """
        X_list = []
        y_list = []

        for record in dataset:
            features = FeatureEngineeringPipeline.extract_features(
                db,
                latitude=record["latitude"],
                longitude=record["longitude"],
                timestamp=record["occurred_at"],
                radius_meters=radius_meters
            )
            X_list.append(features)

            # Target label: high historical risk severity
            severity = record.get("severity", 0.5)
            label = 1 if severity >= 0.75 else 0
            y_list.append(label)

        return np.array(X_list, dtype=np.float64), np.array(y_list, dtype=np.int64)
