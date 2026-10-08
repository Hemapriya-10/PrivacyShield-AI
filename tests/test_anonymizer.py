"""
Unit tests for PII Anonymizer Module.
"""

import pytest
from modules.pii_detector import PIIDetectionResult
from modules.anonymizer import PIIAnonymizer, anonymize_text


@pytest.fixture
def anonymizer():
    return PIIAnonymizer()


def test_redaction_strategy(anonymizer):
    """Test replacing entities with [REDACTED]."""
    text = "Hello Aarav Sharma, your email is aarav@example.com."
    results = [
        PIIDetectionResult(entity_type="PERSON", text="Aarav Sharma", start=6, end=18, score=0.9),
        PIIDetectionResult(entity_type="EMAIL_ADDRESS", text="aarav@example.com", start=34, end=51, score=0.95),
    ]

    anonymized, metadata = anonymizer.anonymize(text, results, strategy="redact")

    assert "[REDACTED]" in anonymized
    assert "Aarav Sharma" not in anonymized
    assert "aarav@example.com" not in anonymized
    assert anonymized == "Hello [REDACTED], your email is [REDACTED]."
    assert metadata["strategy"] == "redact"
    assert metadata["total_anonymized"] == 2


def test_type_based_replacement_strategy(anonymizer):
    """Test replacing entities with indexed labels like [PERSON_1], [EMAIL_1]."""
    text = "Aarav Sharma met Priya Patel in New Delhi."
    results = [
        PIIDetectionResult(entity_type="PERSON", text="Aarav Sharma", start=0, end=12, score=0.9),
        PIIDetectionResult(entity_type="PERSON", text="Priya Patel", start=17, end=28, score=0.9),
        PIIDetectionResult(entity_type="LOCATION", text="New Delhi", start=32, end=41, score=0.9),
    ]

    anonymized, metadata = anonymizer.anonymize(text, results, strategy="type_based")

    assert "[PERSON_1]" in anonymized
    assert "[PERSON_2]" in anonymized
    assert "[LOCATION_1]" in anonymized
    assert anonymized == "[PERSON_1] met [PERSON_2] in [LOCATION_1]."
    assert metadata["strategy"] == "type_based"
    assert metadata["total_anonymized"] == 3


def test_repeated_entity_label_consistency(anonymizer):
    """Test that repeated identical entities receive identical label index."""
    text = "Aarav Sharma called Priya Patel. Later, Aarav Sharma emailed Priya Patel."
    # Aarav Sharma at index 0..12 and 40..52
    # Priya Patel at index 20..31 and 61..72
    results = [
        PIIDetectionResult(entity_type="PERSON", text="Aarav Sharma", start=0, end=12, score=0.9),
        PIIDetectionResult(entity_type="PERSON", text="Priya Patel", start=20, end=31, score=0.9),
        PIIDetectionResult(entity_type="PERSON", text="Aarav Sharma", start=40, end=52, score=0.9),
        PIIDetectionResult(entity_type="PERSON", text="Priya Patel", start=61, end=72, score=0.9),
    ]

    anonymized, metadata = anonymizer.anonymize(text, results, strategy="type_based")

    assert anonymized.count("[PERSON_1]") == 2
    assert anonymized.count("[PERSON_2]") == 2
    assert metadata["entity_counters"]["PERSON"] == 2  # Only 2 unique persons!


def test_empty_results_handling(anonymizer):
    """Test anonymizing text when no PII is detected."""
    text = "This document contains no PII entities."
    anonymized, metadata = anonymizer.anonymize(text, [], strategy="type_based")
    assert anonymized == text
    assert metadata["total_anonymized"] == 0
