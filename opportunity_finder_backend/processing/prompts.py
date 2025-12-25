from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from opportunities.models import Domain, Location, OpportunityType, Specialization


@dataclass(frozen=True)
class TaxonomyContext:
    opportunity_types: list[dict]
    domains: list[dict]
    specializations: list[dict]
    locations: list[dict]

    def to_compact_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def build_taxonomy_context(*, max_locations: int = 400) -> TaxonomyContext:
    """
    Build a controlled taxonomy context that the LLM must select IDs from.

    Note: locations can grow large; for v1 we cap what we send to avoid huge prompts.
    """
    op_types = list(OpportunityType.objects.order_by("id").values("id", "name"))
    domains = list(
        Domain.objects.order_by("id").values("id", "name", "opportunity_type_id")
    )
    specs = list(Specialization.objects.order_by("id").values("id", "name", "domain_id"))

    loc_qs = Location.objects.order_by("id").values("id", "name", "parent_id")
    locations = list(loc_qs[: max_locations or 0]) if max_locations else list(loc_qs)

    return TaxonomyContext(
        opportunity_types=op_types,
        domains=domains,
        specializations=specs,
        locations=locations,
    )


def build_extract_prompt(*, text_en: str, source_url: str | None = None) -> str:
    """
    Prompt body (without schema). The provider will embed schema separately.
    """
    taxonomy = build_taxonomy_context()
    url_text = source_url or ""
    return (
        "You are extracting a structured Opportunity from a raw post.\n"
        "Rules:\n"
        "- You MUST pick op_type_id, domain_id, specialization_id, location_id from the TAXONOMY IDs.\n"
        "- The hierarchy must be consistent:\n"
        "  domain.opportunity_type_id MUST equal op_type_id; specialization.domain_id MUST equal domain_id.\n"
        "- If location is unknown, set location_id = null.\n"
        "- Work mode rules:\n"
        "  - If the text clearly says Remote / Work from home, set work_mode=REMOTE.\n"
        "  - If a specific city/country is mentioned (and remote is NOT mentioned), set work_mode=ONSITE.\n"
        "- If a numeric field is not present, set it to null.\n"
        "- For deadline, output YYYY-MM-DD or null.\n"
        "- If present, extract applicant_gender (FEMALE/MALE/ANY/UNKNOWN), employment_subtype (e.g. PERMANENT),\n"
        "  and compensation (amount + currency + period like MONTH).\n"
        "- Keep description_en concise but informative.\n\n"
        f"TAXONOMY_JSON:\n{taxonomy.to_compact_json()}\n\n"
        f"SOURCE_URL:\n{url_text}\n\n"
        f"TEXT_EN:\n{text_en}"
    )


