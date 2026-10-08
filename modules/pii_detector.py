"""
Hybrid PII Detection Module for PrivacyShield AI.

Combines Microsoft Presidio Analyzer with custom regex recognizers for enhanced
detection of standard and domain-specific entities (e.g., Indian phone numbers).
"""

from dataclasses import dataclass, asdict
import re
from typing import List, Optional, Dict, Any

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern


@dataclass
class PIIDetectionResult:
    """Dataclass holding details of a detected PII entity."""
    entity_type: str
    text: str
    start: int
    end: int
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_indian_phone_recognizer() -> PatternRecognizer:
    """
    Creates a Presidio PatternRecognizer for Indian phone numbers.
    Supports formats: +91 9876543210, +91-98765-43210, 09876543210, 9876543210, etc.
    """
    indian_phone_pattern = Pattern(
        name="indian_phone_pattern",
        regex=r"(?:(?:\+91[\s\-]?)?|(?:0))?[6-9]\d{9}|(?:\+91[\s\-]?)?\d{5}[\s\-]\d{5}",
        score=0.85
    )
    recognizer = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[indian_phone_pattern],
        context=["phone", "call", "mobile", "contact", "tel", "whatsapp", "in"]
    )
    return recognizer


def create_custom_email_recognizer() -> PatternRecognizer:
    """
    Creates a custom high-confidence email regex recognizer to complement spaCy/Presidio defaults.
    """
    email_pattern = Pattern(
        name="custom_email_pattern",
        regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        score=0.95
    )
    recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[email_pattern]
    )
    return recognizer


class HybridPIIDetector:
    """
    Hybrid PII Detector wrapping Microsoft Presidio Analyzer Engine
    with custom regex recognizers and overlap resolution logic.
    """
    
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        # Add custom recognizers
        self.analyzer.registry.add_recognizer(create_indian_phone_recognizer())
        self.analyzer.registry.add_recognizer(create_custom_email_recognizer())

    def analyze_text(
        self,
        text: str,
        score_threshold: float = 0.4,
        entities: Optional[List[str]] = None
    ) -> List[PIIDetectionResult]:
        """
        Analyzes input text and identifies PII entities.

        Args:
            text (str): Input document text.
            score_threshold (float): Minimum confidence score threshold (0.0 - 1.0).
            entities (Optional[List[str]]): Specific entity types to detect.
                Default: ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'LOCATION'].

        Returns:
            List[PIIDetectionResult]: Non-overlapping list of detected PII entities.
        """
        if not text or not text.strip():
            return []

        if entities is None:
            entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"]

        # Map 'LOCATION' to Presidio entity 'LOCATION' / 'GPE' / 'LOC' if applicable
        presidio_entities = list(entities)
        if "LOCATION" in presidio_entities and "GPE" not in presidio_entities:
            presidio_entities.append("GPE")
        if "LOCATION" in presidio_entities and "LOC" not in presidio_entities:
            presidio_entities.append("LOC")

        raw_results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=presidio_entities,
            score_threshold=score_threshold
        )

        # Convert Presidio RecognizerResult objects to PIIDetectionResult
        results = []
        for r in raw_results:
            entity_type = r.entity_type
            # Normalize GPE/LOC to LOCATION for user clarity
            if entity_type in ("GPE", "LOC"):
                entity_type = "LOCATION"

            extracted_text = text[r.start:r.end]
            results.append(
                PIIDetectionResult(
                    entity_type=entity_type,
                    text=extracted_text,
                    start=r.start,
                    end=r.end,
                    score=round(r.score, 2)
                )
            )

        # Fallback regex for Indian phone numbers in case spaCy/Presidio missed them
        if "PHONE_NUMBER" in entities:
            results.extend(self._regex_fallback_indian_phones(text, score_threshold))

        # Fallback regex for Emails
        if "EMAIL_ADDRESS" in entities:
            results.extend(self._regex_fallback_emails(text, score_threshold))

        # Deduplicate and resolve overlapping bounding ranges
        resolved_results = self._resolve_overlaps(results)
        
        # Sort by start position
        resolved_results.sort(key=lambda x: x.start)
        return resolved_results

    def _regex_fallback_indian_phones(self, text: str, threshold: float) -> List[PIIDetectionResult]:
        """Regex fallback for Indian phone numbers."""
        pattern = r"(?:(?:\+91[\s\-]?)?|(?:0))?[6-9]\d{9}|(?:\+91[\s\-]?)?\d{5}[\s\-]\d{5}"
        fallback_results = []
        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            score = 0.85
            if score >= threshold:
                fallback_results.append(
                    PIIDetectionResult(
                        entity_type="PHONE_NUMBER",
                        text=matched_text,
                        start=match.start(),
                        end=match.end(),
                        score=score
                    )
                )
        return fallback_results

    def _regex_fallback_emails(self, text: str, threshold: float) -> List[PIIDetectionResult]:
        """Regex fallback for Email addresses."""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        fallback_results = []
        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            score = 0.95
            if score >= threshold:
                fallback_results.append(
                    PIIDetectionResult(
                        entity_type="EMAIL_ADDRESS",
                        text=matched_text,
                        start=match.start(),
                        end=match.end(),
                        score=score
                    )
                )
        return fallback_results

    def _resolve_overlaps(self, results: List[PIIDetectionResult]) -> List[PIIDetectionResult]:
        """
        Deduplicates overlapping detection ranges.
        If two detections overlap, prefers the one with higher score or longer span.
        """
        if not results:
            return []

        # Sort primarily by start index, secondarily by score (desc), then length (desc)
        sorted_res = sorted(
            results,
            key=lambda item: (item.start, -item.score, -(item.end - item.start))
        )

        resolved: List[PIIDetectionResult] = []
        for item in sorted_res:
            if not resolved:
                resolved.append(item)
                continue

            last = resolved[-1]
            # Check for overlap
            if item.start < last.end:
                # Overlap detected! Compare scores and length
                last_len = last.end - last.start
                item_len = item.end - item.start
                
                # If item has strictly higher score, or equal score with longer length
                if (item.score > last.score) or (item.score == last.score and item_len > last_len):
                    resolved[-1] = item
                # Otherwise keep last
            else:
                # Exact duplicate range check
                if item.start == last.start and item.end == last.end and item.entity_type == last.entity_type:
                    continue
                resolved.append(item)

        return resolved


def get_pii_limitations_notice() -> str:
    """Returns official limitations notice for automated PII detection."""
    return (
        "Notice: Automated PII detection uses statistical NLP models and regex heuristics. "
        "While it covers standard entities (Names, Emails, Phone Numbers, Locations), "
        "it may miss ambiguous contextual identifiers or produce false positives. "
        "Manual verification is recommended for highly sensitive documents."
    )
