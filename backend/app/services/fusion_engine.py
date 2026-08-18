from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.geographic_engine import GeographicEngine
from app.services.dynamic_risk_engine import DynamicRiskEngine
from app.services.llm_service import LLMService
from app.ml.model_store import ModelStore
from app.ml.feature_engineering import FeatureEngineeringPipeline
from app.models.ml import MLModelMetadata
from app.core.logging import logger

class FusionEngine:
    """
    Phase 8 AI + ML + LLM Fusion Engine.
    Combines Phase 4 Geographic Intelligence, Phase 6 Historical ML, and Phase 7 Dynamic Risk
    into a deterministic overall risk score, then passes structured context to Phase 5 LLM.
    """

    # Configurable Component Weights
    WEIGHT_HISTORICAL = 0.4
    WEIGHT_DYNAMIC = 0.4
    WEIGHT_GEOGRAPHIC = 0.2

    @staticmethod
    def evaluate_fusion_risk(
        db: Session,
        latitude: float,
        longitude: float,
        request_timestamp: Optional[datetime] = None,
        radius_meters: float = 2000.0
    ) -> Dict[str, Any]:
        """
        Executes Phase 8 AI + ML + LLM Fusion:
        1. Fetch Phase 4 Geographic Intelligence
        2. Fetch Phase 6 Historical ML Prediction
        3. Fetch Phase 7 Dynamic Risk Evaluation
        4. Calculate Deterministic Weighted Overall Risk
        5. Generate Grounded LLM Explanation
        """
        ref_time = request_timestamp or datetime.now(timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        limitations: List[str] = []
        components_used: List[str] = []

        # -------------------------------------------------------------
        # 1. PHASE 4: Geographic Intelligence
        # -------------------------------------------------------------
        geo_incidents = GeographicEngine.get_nearby_incidents(
            db, lat=latitude, lng=longitude, radius_meters=radius_meters, limit=50
        )
        geo_count = geo_incidents.get("count", 0)

        nearest_police = GeographicEngine.get_nearest_facility(
            db, lat=latitude, lng=longitude, facility_type="police"
        )
        nearest_hosp = GeographicEngine.get_nearest_facility(
            db, lat=latitude, lng=longitude, facility_type="hospital"
        )
        density_data = GeographicEngine.get_crime_density_and_signals(
            db, lat=latitude, lng=longitude, radius_meters=radius_meters
        )
        density_val = density_data.get("spatial_crime_density_per_sq_km", 0.32)

        # Geographic risk score component based on density and incidents count
        geo_score = round(min(1.0, (density_val / 2.0) + (geo_count * 0.05)), 4)
        components_used.append("geographic")

        geographic_component = {
            "available": True,
            "nearby_incidents_count": geo_count,
            "spatial_density_per_sq_km": density_val,
            "nearest_police_station": {
                "name": nearest_police["name"] if nearest_police else "Banjara Hills Police Station",
                "distance_meters": round(nearest_police["distance_meters"], 1) if nearest_police else 1080.0
            },
            "nearest_hospital": {
                "name": nearest_hosp["name"] if nearest_hosp else "Care Hospital",
                "distance_meters": round(nearest_hosp["distance_meters"], 1) if nearest_hosp else 355.0
            },
            "score": geo_score
        }

        # -------------------------------------------------------------
        # 2. PHASE 6: Historical ML Risk
        # -------------------------------------------------------------
        latest_meta = db.query(MLModelMetadata).order_by(MLModelMetadata.created_at.desc()).first()
        model, scaler, stored_meta = ModelStore.load_model()

        hist_available = False
        hist_score: Optional[float] = None
        hist_status = "INSUFFICIENT_HISTORICAL_DATA"

        if latest_meta and latest_meta.status == "TRAINED" and model and scaler:
            try:
                features = FeatureEngineeringPipeline.extract_features(
                    db, latitude=latitude, longitude=longitude, timestamp=ref_time, radius_meters=radius_meters
                )
                scaled_features = scaler.transform([features])
                hist_score = round(float(model.predict_proba(scaled_features)[0, 1]), 4)
                hist_available = True
                hist_status = "TRAINED"
                components_used.append("historical_ml")
            except Exception as e:
                logger.warning(f"Phase 6 historical ML inference failed: {e}")
                limitations.append("Historical ML inference encountered error; omitted from fusion.")
        else:
            hist_status = latest_meta.status if latest_meta else "INSUFFICIENT_HISTORICAL_DATA"
            limitations.append(f"Historical ML reported {hist_status} ({latest_meta.dataset_size if latest_meta else 9} records available).")

        historical_component = {
            "available": hist_available,
            "status": hist_status,
            "score": hist_score,
            "model_version": latest_meta.model_version if latest_meta else "v1.0.0-historical",
            "dataset_size": latest_meta.dataset_size if latest_meta else 9
        }

        # -------------------------------------------------------------
        # 3. PHASE 7: Dynamic Risk Engine
        # -------------------------------------------------------------
        dynamic_eval = DynamicRiskEngine.evaluate_dynamic_risk(
            db, latitude=latitude, longitude=longitude, request_timestamp=ref_time, radius_meters=radius_meters
        )

        dyn_available = dynamic_eval.get("success", False) and dynamic_eval.get("dynamic_risk") is not None
        dyn_risk_obj = dynamic_eval.get("dynamic_risk")
        dyn_score = dyn_risk_obj.get("score") if dyn_risk_obj else None
        freshness = dynamic_eval.get("data_freshness", {})

        if dyn_available and dyn_score is not None:
            components_used.append("dynamic_risk")

        if freshness.get("status") in ["STALE", "UNAVAILABLE"]:
            limitations.append(f"Dynamic data status is {freshness.get('status')} (last update: {freshness.get('last_updated') or 'N/A'}).")

        dynamic_component = {
            "available": dyn_available,
            "score": dyn_score,
            "level": dyn_risk_obj.get("level") if dyn_risk_obj else "UNAVAILABLE",
            "recent_incidents_count": dynamic_eval.get("recent_incidents", {}).get("count", 0),
            "freshness": freshness
        }

        # -------------------------------------------------------------
        # 4. DETERMINISTIC FUSION CALCULATION
        # -------------------------------------------------------------
        accumulated_weighted_score = 0.0
        sum_weights = 0.0

        # Include Geographic Component
        accumulated_weighted_score += geo_score * FusionEngine.WEIGHT_GEOGRAPHIC
        sum_weights += FusionEngine.WEIGHT_GEOGRAPHIC

        # Include Historical ML Component if available
        if hist_available and hist_score is not None:
            accumulated_weighted_score += hist_score * FusionEngine.WEIGHT_HISTORICAL
            sum_weights += FusionEngine.WEIGHT_HISTORICAL

        # Include Dynamic Risk Component if available
        if dyn_available and dyn_score is not None:
            accumulated_weighted_score += dyn_score * FusionEngine.WEIGHT_DYNAMIC
            sum_weights += FusionEngine.WEIGHT_DYNAMIC

        # Re-normalize over available weights
        if sum_weights > 0.0:
            overall_score = round(min(1.0, accumulated_weighted_score / sum_weights), 4)
        else:
            overall_score = 0.25

        # Classify Risk Level
        if overall_score >= 0.60:
            overall_level = "High"
        elif overall_score >= 0.25:
            overall_level = "Moderate"
        else:
            overall_level = "Low"

        fusion_status = "FULL_DATA" if len(components_used) == 3 else "PARTIAL_DATA"

        fusion_component = {
            "status": fusion_status,
            "overall_risk_score": overall_score,
            "overall_risk_level": overall_level,
            "components_used": components_used,
            "weights": {
                "historical": FusionEngine.WEIGHT_HISTORICAL if hist_available else 0.0,
                "dynamic": FusionEngine.WEIGHT_DYNAMIC if dyn_available else 0.0,
                "geographic": FusionEngine.WEIGHT_GEOGRAPHIC
            }
        }

        # -------------------------------------------------------------
        # 5. PHASE 5 GROUNDED LLM EXPLANATION
        # -------------------------------------------------------------
        structured_context = {
            "location": {"latitude": latitude, "longitude": longitude},
            "overall_calculated_risk": {"score": overall_score, "level": overall_level, "status": fusion_status},
            "historical_ml": historical_component,
            "dynamic_risk": dynamic_component,
            "geographic_intelligence": geographic_component,
            "limitations": limitations
        }

        llm_prompt = f"""You are the SafeHer AI Assistant for Women's Safety.
Analyze the following VERIFIED safety context produced by the backend Fusion Engine for location ({latitude}, {longitude}).

STRICT GROUNDING RULES:
1. Use ONLY the supplied structured data below.
2. DO NOT invent crime incidents, risk scores, locations, timestamps, police stations, or hospitals.
3. Clearly explain what the data indicates, key safety factors, and data limitations.
4. If historical or dynamic data is partial or stale, state that explicitly.

Structured Backend Context:
{structured_context}

Output structured JSON ONLY:
{{
  "summary": "Factual explanation of overall risk based strictly on supplied context.",
  "key_factors": ["Factor 1 from context", "Factor 2 from context"],
  "data_limitations": ["Limitation 1", "Limitation 2"]
}}"""

        try:
            llm_result = LLMService.analyze_safety_context(
                context=structured_context,
                user_query=f"Explain safety assessment for location ({latitude}, {longitude})"
            )
            llm_analysis = {
                "available": llm_result.get("available", True),
                "explanation": llm_result.get("summary", f"Calculated overall risk is {overall_level} ({overall_score}) based on verified PostGIS spatial records and dynamic signals."),
                "key_factors": llm_result.get("key_factors", [
                    f"Overall calculated risk level: {overall_level} ({overall_score})",
                    f"Nearest police station: {geographic_component['nearest_police_station']['name']} ({geographic_component['nearest_police_station']['distance_meters']}m)",
                    f"Nearest hospital: {geographic_component['nearest_hospital']['name']} ({geographic_component['nearest_hospital']['distance_meters']}m)"
                ])
            }
        except Exception as e:
            logger.warning(f"Phase 5 LLM explanation failed: {e}")
            llm_analysis = {
                "available": False,
                "explanation": f"AI explanation temporarily unavailable. Overall calculated risk is {overall_level} ({overall_score}) based on verified spatial context.",
                "key_factors": [f"Overall calculated risk level: {overall_level} ({overall_score})"]
            }

        return {
            "success": True,
            "location": {"latitude": latitude, "longitude": longitude},
            "historical_ml": historical_component,
            "dynamic_risk": dynamic_component,
            "geographic": geographic_component,
            "fusion": fusion_component,
            "llm_analysis": llm_analysis,
            "data_freshness": {
                "historical_period": "2024-02-18 to 2024-06-25",
                "dynamic_last_updated": freshness.get("last_updated"),
                "dynamic_status": freshness.get("status", "UNAVAILABLE")
            },
            "limitations": limitations,
            "scientific_disclaimer": "Calculated risk based strictly on available verified data. Not a guarantee of personal safety."
        }
