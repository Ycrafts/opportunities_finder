from __future__ import annotations

from typing import Any

from opportunities.models import Opportunity


def opportunity_extract_schema() -> dict[str, Any]:
    """
    JSON schema for LLM extraction output (v1).

    Important: we use *_id fields so the model must pick from our controlled taxonomy.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title",
            "op_type_id",
            "domain_id",
            "specialization_id",
            "work_mode",
            "employment_type",
            "experience_level",
            "deadline",
            "min_compensation",
            "max_compensation",
            "location_id",
            "organization",
            "source_url",
            "description_en",
            "confidence",
        ],
        "properties": {
            "title": {"type": "string"},
            "organization": {"type": ["string", "null"]},
            "source_url": {"type": ["string", "null"]},
            "description_en": {"type": ["string", "null"]},
            "op_type_id": {"type": "integer", "minimum": 1},
            "domain_id": {"type": "integer", "minimum": 1},
            "specialization_id": {"type": "integer", "minimum": 1},
            "location_id": {"type": ["integer", "null"], "minimum": 1},
            "work_mode": {"type": "string", "enum": [c for c, _ in Opportunity.WorkMode.choices]},
            "employment_type": {
                "type": "string",
                "enum": [c for c, _ in Opportunity.EmploymentType.choices],
            },
            "experience_level": {
                "type": "string",
                "enum": [c for c, _ in Opportunity.ExperienceLevel.choices],
            },
            # ISO date string or null
            "deadline": {"type": ["string", "null"], "pattern": r"^\d{4}-\d{2}-\d{2}$"},
            "min_compensation": {"type": ["integer", "null"]},
            "max_compensation": {"type": ["integer", "null"]},
            "applicant_gender": {
                "type": ["string", "null"],
                "enum": ["FEMALE", "MALE", "ANY", "UNKNOWN", None],
            },
            "employment_subtype": {"type": ["string", "null"]},
            "compensation": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "required": ["amount", "currency", "period"],
                "properties": {
                    "amount": {"type": ["integer", "null"]},
                    "currency": {"type": ["string", "null"]},
                    "period": {
                        "type": ["string", "null"],
                        "enum": ["MONTH", "YEAR", "WEEK", "DAY", "ONE_TIME", "UNKNOWN", None],
                    },
                },
            },
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "notes": {"type": ["string", "null"]},
        },
    }


