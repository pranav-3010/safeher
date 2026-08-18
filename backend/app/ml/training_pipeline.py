import numpy as np
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from sqlalchemy.orm import Session
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_absolute_error, mean_squared_error

from app.ml.data_pipeline import HistoricalDataPipeline
from app.ml.feature_engineering import FeatureEngineeringPipeline, FEATURE_NAMES
from app.ml.model_store import ModelStore
from app.models.ml import MLModelMetadata
from app.core.logging import logger

MIN_DATASET_THRESHOLD = 50  # Statistical threshold for reliable model training

class BaselineModel:
    """Historical Frequency Baseline Model"""
    def __init__(self):
        self.mean_risk = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray):
        if len(y) > 0:
            self.mean_risk = float(np.mean(y))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(shape=(len(X),), fill_value=1 if self.mean_risk >= 0.5 else 0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        proba_1 = np.full(shape=(len(X), 1), fill_value=self.mean_risk)
        proba_0 = 1.0 - proba_1
        return np.hstack([proba_0, proba_1])


class HistoricalMLTrainer:
    """
    ML Training Pipeline for Phase 6 Historical Model.
    Enforces strict temporal split, baseline evaluation, candidate training, evaluation, and DB recording.
    """

    @staticmethod
    def run_training_pipeline(db: Session) -> Dict[str, Any]:
        """
        Executes full training pipeline:
        1. Ingest & Validate Data
        2. Extract Features
        3. Enforce Temporal Train/Val/Test Split
        4. Evaluate Baseline vs ML Candidates
        5. Persist Model & Record Metadata in DB
        """
        start_time = datetime.now(timezone.utc)
        dataset, quality_report = HistoricalDataPipeline.load_and_validate_dataset(db)
        dataset_size = len(dataset)

        logger.info(f"Loaded {dataset_size} valid historical records for ML pipeline.")

        # Check if verified dataset size is sufficient
        if dataset_size < MIN_DATASET_THRESHOLD:
            logger.warning(
                f"Insufficient verified historical data for reliable ML training ({dataset_size} records available, minimum threshold is {MIN_DATASET_THRESHOLD})."
            )

            metadata_record = MLModelMetadata(
                model_version="v1.0.0-historical",
                algorithm="RandomForestClassifier",
                training_start=start_time,
                training_end=datetime.now(timezone.utc),
                dataset_size=dataset_size,
                target_definition="Historical Crime Risk Severity (>= 0.75)",
                metrics={
                    "data_quality": quality_report,
                    "threshold_status": "INSUFFICIENT_DATA",
                    "note": f"Dataset contains {dataset_size} verified historical records. System pipeline is ready for future ingestion."
                },
                status="INSUFFICIENT_DATA"
            )
            db.add(metadata_record)
            db.commit()
            db.refresh(metadata_record)

            # Persist fallback metadata model bundle
            fallback_model = BaselineModel()
            fallback_scaler = StandardScaler()
            ModelStore.save_model(fallback_model, fallback_scaler, metadata_record.to_dict())

            return {
                "success": False,
                "status": "INSUFFICIENT_DATA",
                "message": f"Insufficient verified historical data for reliable ML training ({dataset_size} records available).",
                "dataset_size": dataset_size,
                "quality_report": quality_report,
                "model_version": "v1.0.0-historical"
            }

        # 2. Sort Dataset Temporally to Prevent Data Leakage
        sorted_dataset = sorted(dataset, key=lambda d: d["occurred_at"])
        X_raw, y = FeatureEngineeringPipeline.build_feature_matrix(db, sorted_dataset)

        # Temporal Train/Validation/Test Split (70% Train, 15% Val, 15% Test)
        train_idx = int(dataset_size * 0.70)
        val_idx = int(dataset_size * 0.85)

        X_train_raw, y_train = X_raw[:train_idx], y[:train_idx]
        X_val_raw, y_val = X_raw[train_idx:val_idx], y[train_idx:val_idx]
        X_test_raw, y_test = X_raw[val_idx:], y[val_idx:]

        # Scale Features
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train_raw)
        X_val = scaler.transform(X_val_raw)
        X_test = scaler.transform(X_test_raw)

        # 3. Train Baseline Model
        baseline = BaselineModel()
        baseline.fit(X_train, y_train)
        y_pred_base = baseline.predict(X_test)
        base_acc = float(accuracy_score(y_test, y_pred_base))

        # 4. Train Candidate Models
        candidates = {
            "RandomForestClassifier": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
            "GradientBoostingClassifier": GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42),
            "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42)
        }

        best_model_name = "RandomForestClassifier"
        best_model = None
        best_f1 = -1.0
        best_metrics = {}

        for name, clf in candidates.items():
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            y_proba = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            mae = float(mean_absolute_error(y_test, y_proba))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_proba)))
            try:
                auc = float(roc_auc_score(y_test, y_proba))
            except Exception:
                auc = 0.5

            metrics = {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "roc_auc": auc,
                "mae": mae,
                "rmse": rmse,
                "baseline_accuracy": base_acc
            }

            if f1 > best_f1:
                best_f1 = f1
                best_model_name = name
                best_model = clf
                best_metrics = metrics

        # 5. Persist Model and Metadata
        end_time = datetime.now(timezone.utc)
        metadata_record = MLModelMetadata(
            model_version="v1.0.0-historical",
            algorithm=best_model_name,
            training_start=start_time,
            training_end=end_time,
            dataset_size=dataset_size,
            target_definition="Historical Crime Risk Severity (>= 0.75)",
            metrics=best_metrics,
            status="TRAINED"
        )
        db.add(metadata_record)
        db.commit()
        db.refresh(metadata_record)

        ModelStore.save_model(best_model, scaler, metadata_record.to_dict())

        return {
            "success": True,
            "status": "TRAINED",
            "model_version": "v1.0.0-historical",
            "algorithm": best_model_name,
            "dataset_size": dataset_size,
            "metrics": best_metrics,
            "quality_report": quality_report
        }
