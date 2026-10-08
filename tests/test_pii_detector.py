"""
Unit tests for Hybrid PII Detector Module.
"""

import pytest
from modules.pii_detector import HybridPIIDetector, get_pii_limitations_notice


@pytest.fixture
def detector():
    return HybridPIIDetector()


def test_empty_input(detector):
    """Test empty string and whitespace handling."""
    assert detector.analyze_text("") == []
    assert detector.analyze_text("   \n\t  ") == []


def test_email_detection(detector):
    """Test custom and Presidio email address detection."""
    text = "Please send inquiries to contact.us@example.org or support@test-domain.co.in."
    results = detector.analyze_text(text, score_threshold=0.4, entities=["EMAIL_ADDRESS"])
    
    detected_texts = [r.text for r in results]
    assert "contact.us@example.org" in detected_texts
    assert "support@test-domain.co.in" in detected_texts
    for r in results:
        assert r.entity_type == "EMAIL_ADDRESS"


def test_indian_phone_detection(detector):
    """Test Indian phone number detection in various formats."""
    text = "Call us at +91 98765 43210 or 09876543210 or 9123456789."
    results = detector.analyze_text(text, score_threshold=0.4, entities=["PHONE_NUMBER"])

    detected_texts = [r.text for r in results]
    assert any("98765 43210" in t for t in detected_texts)
    assert any("09876543210" in t for t in detected_texts)
    assert any("9123456789" in t for t in detected_texts)


def test_person_and_location_detection(detector):
    """Test person name and location detection."""
    text = "Aarav Sharma works at tech company in New Delhi."
    results = detector.analyze_text(text, score_threshold=0.3, entities=["PERSON", "LOCATION"])

    detected_types = {r.entity_type for r in results}
    detected_texts = [r.text for r in results]

    # Verify entities are present
    assert any("Aarav" in t or "Sharma" in t for t in detected_texts)
    assert any("New Delhi" in t or "Delhi" in t for t in detected_texts)


def test_deduplication_and_overlaps(detector):
    """Test that overlapping detections are cleanly resolved without duplicates."""
    text = "Contact info: john.doe@example.com, phone +91 9876543210."
    results = detector.analyze_text(text)

    # Check start indices are unique / non-overlapping
    for i in range(len(results) - 1):
        assert results[i].end <= results[i + 1].start, (
            f"Overlap found between '{results[i].text}' and '{results[i+1].text}'"
        )


def test_limitations_notice():
    """Test limitations notice content."""
    notice = get_pii_limitations_notice()
    assert "Notice:" in notice
    assert "statistical NLP" in notice
