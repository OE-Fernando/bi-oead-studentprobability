from __future__ import annotations

from typing import Any, Dict, Optional

from get_dynamodb_item import get_item_by_pk


_DEFAULT_FEATURES: Dict[str, str] = {
    "enrollment":          "U",
    "studentHistory":      "0-0",
    "country_iso":         "XX",
    "isb2b":               "0",
    "gender":              "U",
    "ageGroup":            "U",
    "studentLevelNumber":  "0",
}


class StudentService:
    """Resolves student-level features from a person identifier.

    The DynamoDB connection is created once at module load (in
    get_dynamodb_item.py) and reused across Lambda invocations.

    Supply a ``db_client`` with a ``get_student_features(pk: str) -> dict``
    method to override the default DynamoDB path (useful in unit tests).
    """

    def __init__(self, db_client: Optional[Any] = None) -> None:
        self._db_client = db_client

    def extract_student_features(self, person_id: int) -> Dict[str, str]:
        """Return a dict of categorical student features keyed by feature name.

        Keys returned:
            enrollment, studentHistory, country_iso, isb2b,
            gender, ageGroup, studentLevelNumber
        """
        PK = f"S#{person_id}"

        if self._db_client is not None:
            raw = self._db_client.get_student_features(PK)
            return self._normalize(raw)

        item = get_item_by_pk(PK)
        if item is None:
            return dict(_DEFAULT_FEATURES)
        return self._normalize(item)

    @staticmethod
    def _normalize(raw: Dict[str, Any]) -> Dict[str, str]:
        """Coerce all feature values to str and fill missing keys with defaults."""
        result = dict(_DEFAULT_FEATURES)
        for key in result:
            if key in raw and raw[key] is not None:
                result[key] = str(raw[key])
        return result
