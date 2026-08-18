import sys
import json
from dotenv import load_dotenv
load_dotenv(".env")

from app.database.session import SessionLocal
from app.ml.training_pipeline import HistoricalMLTrainer

def main():
    print("=== SafeHer Phase 6: Historical ML Model Training Pipeline ===")
    db = SessionLocal()
    try:
        results = HistoricalMLTrainer.run_training_pipeline(db)
        print("\n=== Pipeline Execution Summary ===")
        print(json.dumps(results, indent=2))
    finally:
        db.close()

if __name__ == "__main__":
    main()
