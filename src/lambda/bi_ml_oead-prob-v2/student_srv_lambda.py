from __future__ import annotations

from typing import Any, Dict, Optional


UNKNOWN = "unknown"

_MOCK_STUDENTS: Dict[int, Dict[str, str]] = {
    1001: {
        "enrollment":          "re-enrolled",
        "studentHistory":      "regular",
        "country_iso":         "MX",
        "isb2b":               "0",
        "gender":              "F",
        "ageGroup":            "25-34",
        "studentLevelNumber":  "3",
    },
    1002: {
        "enrollment":          "new",
        "studentHistory":      "first-time",
        "country_iso":         "US",
        "isb2b":               "1",
        "gender":              "M",
        "ageGroup":            "18-24",
        "studentLevelNumber":  "1",
    },
}

_DEFAULT_FEATURES: Dict[str, str] = {
    "enrollment":          UNKNOWN,
    "studentHistory":      UNKNOWN,
    "country_iso":         UNKNOWN,
    "isb2b":               "0",
    "gender":              UNKNOWN,
    "ageGroup":            UNKNOWN,
    "studentLevelNumber":  "0",
}


class StudentService:
    """Resolves student-level features from a person identifier.

    In production, supply a ``db_client`` that exposes a
    ``get_student_features(person_id: int) -> dict`` method backed by
    the actual student data store.  When no client is provided the
    service falls back to a small in-memory mock table, which is
    sufficient for local development and unit tests.
    """

    def __init__(self, db_client: Optional[Any] = None) -> None:
        self._db_client = db_client

    def extract_student_features(self, person_id: int) -> Dict[str, str]:
        """Return a dict of categorical student features keyed by feature name.

        Keys returned:
            enrollment, studentHistory, country_iso, isb2b,
            gender, ageGroup, studentLevelNumber
        """
        if self._db_client is not None:
            raw = self._db_client.get_student_features(person_id)
            return self._normalize(raw)

        return dict(_MOCK_STUDENTS.get(person_id, _DEFAULT_FEATURES))

    @staticmethod
    def _normalize(raw: Dict[str, Any]) -> Dict[str, str]:
        """Coerce all feature values to str and fill missing keys with defaults."""
        result = dict(_DEFAULT_FEATURES)
        for key in result:
            if key in raw and raw[key] is not None:
                result[key] = str(raw[key])
        return result
