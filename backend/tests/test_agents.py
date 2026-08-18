import pytest
from unittest.mock import patch, MagicMock
from app.services.data_processing import validate_coordinates, generate_content_hash, clean_text_string
from app.agents.government_agent import GovernmentDataAgent
from app.agents.news_agent import NewsDataAgent
from app.agents.osm_agent import OSMAgent
from app.agents.community_agent import CommunityDataAgent
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_coordinate_validation():
    assert validate_coordinates(17.3850, 78.4867) is True
    assert validate_coordinates(-90.0, 180.0) is True
    assert validate_coordinates(91.0, 78.4867) is False
    assert validate_coordinates(17.3850, -181.0) is False
    assert validate_coordinates(None, 78.4867) is False


def test_content_hash_deduplication():
    hash1 = generate_content_hash("Google News", "Safety Report Title", "http://news.com/1")
    hash2 = generate_content_hash("Google News", "Safety Report Title", "http://news.com/1")
    hash3 = generate_content_hash("Google News", "Different Title", "http://news.com/1")
    
    assert hash1 == hash2
    assert hash1 != hash3


def test_clean_text_string():
    assert clean_text_string("  Hello   World  \n ") == "Hello World"
    assert clean_text_string("") is None
    assert clean_text_string(None) is None


def test_government_agent_parsing_and_validation():
    agent = GovernmentDataAgent()
    sample_json = '[{"id": "GOV-001", "incident_type": "Theft", "latitude": 17.3850, "longitude": 78.4867}]'
    
    raw = agent.fetch(raw_content=sample_json, file_format="json")
    assert len(raw) == 1
    
    valid, rejected = agent.validate(raw)
    assert len(valid) == 1
    assert rejected == 0
    assert valid[0]["incident_type"] == "Theft"
    assert valid[0]["latitude"] == 17.3850


def test_news_agent_validation():
    agent = NewsDataAgent()
    raw = [
        {"title": "Women Safety News", "publisher": "The Times", "url": "https://news.com/a1"},
        {"title": "", "publisher": "The Times", "url": "https://news.com/a2"} # Invalid missing title
    ]
    valid, rejected = agent.validate(raw)
    assert len(valid) == 1
    assert rejected == 1
    assert valid[0]["title"] == "Women Safety News"


def test_osm_agent_validation():
    agent = OSMAgent()
    raw_node = [{"type": "node", "id": 1001, "lat": 17.3850, "lon": 78.4867, "tags": {"amenity": "police", "name": "City Police Station"}}]
    valid, rejected = agent.validate(raw_node)
    assert len(valid) == 1
    assert rejected == 0
    assert valid[0]["osm_id"] == "node/1001"


def test_community_agent_validation():
    agent = CommunityDataAgent()
    raw_valid = [{"report_type": "unlit_road", "description": "Streetlight broken", "latitude": 17.3850, "longitude": 78.4867}]
    raw_invalid_coords = [{"report_type": "unlit_road", "description": "Streetlight broken", "latitude": 100.0, "longitude": 78.4867}]
    
    valid1, rej1 = agent.validate(raw_valid)
    assert len(valid1) == 1 and rej1 == 0
    
    valid2, rej2 = agent.validate(raw_invalid_coords)
    assert len(valid2) == 0 and rej2 == 1


def test_data_sources_api_endpoints():
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = []
    
    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/data/sources")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
    finally:
        app.dependency_overrides.clear()


def test_data_quality_api_endpoint():
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    
    from app.database.session import get_db
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/data/quality")
        assert res.status_code == 200
        data = res.json()
        assert "ingested_records" in data
        assert "data_quality_metrics" in data
    finally:
        app.dependency_overrides.clear()
