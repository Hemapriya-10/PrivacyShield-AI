"""
PII Anonymization Module for PrivacyShield AI.

Implements Redaction and Type-Based Replacement strategies with entity mapping consistency.
"""

from typing import List, Tuple, Dict, Any
from modules.pii_detector import PIIDetectionResult


class PIIAnonymizer:
    """
    Anonymizes text given detected PII entities and a selected strategy.
    Supported strategies:
        - "redact": Replaces entities with [REDACTED].
        - "type_based": Replaces entities with indexed labels like [PERSON_1], [EMAIL_1], etc.
    """

    def anonymize(
        self,
        text: str,
        detection_results: List[PIIDetectionResult],
        strategy: str = "type_based"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Anonymizes input text using the specified strategy.

        Args:
            text (str): Original document text.
            detection_results (List[PIIDetectionResult]): List of detected entities.
            strategy (str): "type_based" or "redact".

        Returns:
            Tuple[str, Dict[str, Any]]:
                - Anonymized text string.
                - Metadata dict containing entity replacement mapping and counts.
        """
        if not text or not detection_results:
            return text, {"replacement_map": {}, "total_anonymized": 0, "strategy": strategy}

        if strategy not in ("type_based", "redact"):
            raise ValueError(f"Unknown anonymization strategy '{strategy}'. Supported: 'type_based', 'redact'")

        # Filter out invalid or out-of-bounds results
        valid_results = [
            r for r in detection_results
            if 0 <= r.start < len(text) and r.start < r.end <= len(text)
        ]

        if strategy == "redact":
            return self._apply_redaction(text, valid_results)
        else:
            return self._apply_type_based_replacement(text, valid_results)

    def _apply_redaction(
        self, text: str, results: List[PIIDetectionResult]
    ) -> Tuple[str, Dict[str, Any]]:
        """Replaces all PII entities with [REDACTED]."""
        # Sort in reverse order of start index to safely slice string without index shifting
        sorted_results = sorted(results, key=lambda r: r.start, reverse=True)
        
        anonymized_text = text
        replacement_map = {}
        
        for r in sorted_results:
            original_snippet = text[r.start:r.end]
            replacement_label = "[REDACTED]"
            
            anonymized_text = (
                anonymized_text[:r.start] + replacement_label + anonymized_text[r.end:]
            )
            replacement_map[original_snippet] = replacement_label

        metadata = {
            "replacement_map": replacement_map,
            "total_anonymized": len(results),
            "strategy": "redact"
        }
        return anonymized_text, metadata

    def _apply_type_based_replacement(
        self, text: str, results: List[PIIDetectionResult]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Replaces PII entities with labels like [PERSON_1], [EMAIL_1], preserving
        consistency across repeated identical entities.
        """
        # First pass: Build consistent mapping for unique entities per type
        entity_counters: Dict[str, int] = {}
        entity_label_map: Dict[Tuple[str, str], str] = {}  # (entity_type, text_lower) -> label
        full_replacement_map: Dict[str, str] = {}  # original_text -> label

        # Sort chronologically by start index to assign _1, _2 in order of appearance
        chrono_results = sorted(results, key=lambda r: r.start)

        for r in chrono_results:
            original_snippet = text[r.start:r.end]
            entity_key = (r.entity_type, original_snippet.strip().lower())

            if entity_key not in entity_label_map:
                current_count = entity_counters.get(r.entity_type, 0) + 1
                entity_counters[r.entity_type] = current_count
                label = f"[{r.entity_type}_{current_count}]"
                entity_label_map[entity_key] = label
            
            full_replacement_map[original_snippet] = entity_label_map[entity_key]

        # Second pass: Replace snippets in reverse order of start index to maintain correct indices
        reverse_results = sorted(results, key=lambda r: r.start, reverse=True)
        anonymized_text = text

        for r in reverse_results:
            original_snippet = text[r.start:r.end]
            entity_key = (r.entity_type, original_snippet.strip().lower())
            label = entity_label_map[entity_key]

            anonymized_text = (
                anonymized_text[:r.start] + label + anonymized_text[r.end:]
            )

        metadata = {
            "replacement_map": full_replacement_map,
            "entity_counters": entity_counters,
            "total_anonymized": len(results),
            "strategy": "type_based"
        }
        return anonymized_text, metadata


def anonymize_text(
    text: str,
    detection_results: List[PIIDetectionResult],
    strategy: str = "type_based"
) -> Tuple[str, Dict[str, Any]]:
    """Helper function for simple one-off anonymization calls."""
    anonymizer = PIIAnonymizer()
    return anonymizer.anonymize(text, detection_results, strategy=strategy)
