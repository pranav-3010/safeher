import os
import joblib
from typing import Any, Dict, Optional, Tuple
from app.core.logging import logger

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
MODEL_PATH = os.path.join(MODEL_DIR, "historical_risk_model.joblib")

class ModelStore:
    """
    Model Persistence Store for Phase 6 Historical ML Model.
    Serializes and deserializes model weights, scalers, and metadata to disk.
    """

    @staticmethod
    def save_model(
        model: Any,
        scaler: Any,
        metadata: Dict[str, Any],
        filepath: str = MODEL_PATH
    ) -> bool:
        """
        Saves model weights, scaler, and metadata dictionary to joblib file.
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            bundle = {
                "model": model,
                "scaler": scaler,
                "metadata": metadata
            }
            joblib.dump(bundle, filepath)
            logger.info(f"Successfully saved ML model bundle to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save ML model bundle: {e}")
            return False

    @staticmethod
    def load_model(filepath: str = MODEL_PATH) -> Tuple[Optional[Any], Optional[Any], Optional[Dict[str, Any]]]:
        """
        Loads model weights, scaler, and metadata from joblib file.
        """
        if not os.path.exists(filepath):
            logger.warning(f"Model file {filepath} does not exist.")
            return None, None, None

        try:
            bundle = joblib.load(filepath)
            return bundle.get("model"), bundle.get("scaler"), bundle.get("metadata")
        except Exception as e:
            logger.error(f"Failed to load ML model bundle: {e}")
            return None, None, None
