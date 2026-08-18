import sys
import os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.agents.osm_agent import OSMAgent
from app.agents.news_agent import NewsDataAgent
from app.agents.government_agent import GovernmentDataAgent


def run_all_real_ingestion():
    """
    Triggers real-world data ingestion agents to populate live Supabase tables:
    - OpenStreetMap (Roads, Police Stations, Hospitals, Metro, Petrol Stations)
    - Google News RSS (Women Safety News Articles)
    """
    db = SessionLocal()
    try:
        print("🚀 Starting Real-World Data Ingestion for Supabase...\n")

        # 1. Ingest Real OpenStreetMap GIS Data for Hyderabad Bounding Box
        print("1️⃣ Ingesting real OpenStreetMap geographic data (Roads & Emergency Facilities)...")
        osm_agent = OSMAgent()
        osm_result = osm_agent.run_pipeline(db, bbox=(17.35, 78.45, 17.42, 78.52))
        print("   Result:", osm_result)

        # 2. Ingest Real News RSS Safety Articles
        print("\n2️⃣ Ingesting real public News RSS safety articles...")
        news_agent = NewsDataAgent()
        news_result = news_agent.run_pipeline(db, rss_url="https://news.google.com/rss/search?q=women+safety+india&hl=en-IN")
        print("   Result:", news_result)

        print("\n✅ Ingestion complete! Check your Supabase Table Editor now.")

    except Exception as e:
        print("❌ Ingestion error:", e)
    finally:
        db.close()


if __name__ == "__main__":
    run_all_real_ingestion()
