import pytest
from unittest.mock import MagicMock
from app.agents.hyderabad_news_agent import HyderabadNewsAgent


def test_hyderabad_location_and_crime_nlp_extraction():
    agent = HyderabadNewsAgent()

    # Test Banjara Hills snatching report
    loc, coords, crime_type, severity = agent.extract_hyderabad_location_and_crime(
        "Chain snatching reported near Banjara Hills main road"
    )

    assert loc == "Banjara Hills"
    assert coords == (17.4150, 78.4350)
    assert "Snatching" in crime_type
    assert severity >= 0.60

    # Test Hitech City harassment report
    loc_h, coords_h, crime_h, sev_h = agent.extract_hyderabad_location_and_crime(
        "Police arrest suspect for harassment in Hitech City IT corridor"
    )

    assert loc_h == "Hitech City"
    assert coords_h == (17.4435, 78.3772)
    assert "Harassment" in crime_h
    assert sev_h >= 0.70


def test_hyderabad_news_agent_validation():
    agent = HyderabadNewsAgent()

    raw_records = [
        {
            "title": "Chain snatching incident in Jubilee Hills area",
            "publisher": "Times of India",
            "url": "https://example.com/news/1",
            "description": "Jubilee Hills police registered case.",
            "published_at": "Tue, 18 Aug 2026 10:00:00 GMT"
        },
        {
            "title": "",
            "publisher": "Invalid News",
            "url": None
        }
    ]

    valid, rejected = agent.validate(raw_records)

    assert len(valid) == 1
    assert rejected == 1
    assert valid[0]["extracted_location"] == "Jubilee Hills"
    assert valid[0]["coords"] == (17.4316, 78.4071)
    assert valid[0]["crime_type"] == "Chain Snatching / Robbery"
