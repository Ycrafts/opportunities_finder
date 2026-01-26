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

    # Include opportunity_type info in domains for clarity
    domains = list(
        Domain.objects.select_related('opportunity_type')
        .order_by("id")
        .values("id", "name", "opportunity_type_id", "opportunity_type__name")
    )

    # Include domain and opportunity_type info in specializations
    specs = list(
        Specialization.objects.select_related('domain__opportunity_type')
        .order_by("id")
        .values(
            "id", "name", "domain_id",
            "domain__name", "domain__opportunity_type__name"
        )
    )

    loc_qs = Location.objects.order_by("id").values("id", "name", "parent_id")
    locations = list(loc_qs[: max_locations or 0]) if max_locations else list(loc_qs)

    return TaxonomyContext(
        opportunity_types=op_types,
        domains=domains,
        specializations=specs,
        locations=locations,
    )


def _build_taxonomy_examples() -> str:
    """Build examples of valid taxonomy combinations."""
    # Get a few examples of valid combinations
    examples = []
    domains_with_types = Domain.objects.select_related('opportunity_type').order_by('?')[:3]

    for domain in domains_with_types:
        specs = list(Specialization.objects.filter(domain=domain)[:2])
        if specs:
            examples.append(
                f"  • OpType '{domain.opportunity_type.name}' (id:{domain.opportunity_type.id}) "
                f"→ Domain '{domain.name}' (id:{domain.id}) "
                f"→ Specializations: {', '.join([f'{s.name}(id:{s.id})' for s in specs])}"
            )

    if examples:
        return "EXAMPLES OF VALID COMBINATIONS:\n" + "\n".join(examples) + "\n\n"
    return ""


def build_extract_prompt(*, text_en: str, source_url: str | None = None) -> str:
    """
    Prompt body (without schema). The provider will embed schema separately.
    """
    taxonomy = build_taxonomy_context()
    url_text = source_url or ""

    # Build a clearer taxonomy explanation
    taxonomy_explanation = (
        "TAXONOMY SELECTION RULES (CRITICAL - FOLLOW THIS ORDER):\n"
        "1. FIRST: Choose op_type_id from opportunity_types list\n"
        "2. SECOND: Choose domain_id ONLY from domains where opportunity_type_id matches your chosen op_type_id\n"
        "3. THIRD: Choose specialization_id ONLY from specializations where domain_id matches your chosen domain_id\n"
        "4. FOURTH: Choose location_id from locations list (or null if unknown)\n\n"
        "VIOLATION WILL CAUSE FAILURE - Always check relationships before selecting IDs!\n"
    )

    examples = _build_taxonomy_examples()

    return (
        "You are extracting a structured Opportunity from a raw post.\n\n"
        f"{taxonomy_explanation}"
        f"{examples}"
        "COMMON PATTERNS TO RECOGNIZE:\n"
        "- SCHOLARSHIP opportunities: Look for words like 'scholarship', 'fully funded', 'grant', 'award', 'stipend'\n"
        "  Set op_type_id to SCHOLARSHIP id, then choose appropriate domain (Masters, PhD, Bachelors, etc.)\n"
        "- JOB opportunities: Look for salary/compensation, job title, employment terms\n"
        "  Set op_type_id to JOB id, then choose domain (Software, Engineering, etc.)\n"
        "- INTERNSHIP opportunities: Look for 'internship', 'intern', training programs\n"
        "- TRAINING opportunities: Look for 'training', 'course', 'workshop', 'certification'\n\n"
        "EXTRACTION RULES:\n"
        "- If you cannot confidently pick a specific domain/specialization for the chosen opportunity type,\n"
        "  choose the catch-all Domain 'Other' and Specialization 'General' for that opportunity type.\n"
        "- You MUST pick IDs from the TAXONOMY_JSON below. NEVER make up IDs!\n"
        "- CRITICAL: opportunity_type vs employment_type:\n"
        "  - opportunity_type: What kind of opportunity is this? (JOB, SCHOLARSHIP, INTERNSHIP, TRAINING)\n"
        "  - employment_type: For JOBS only - how is the person employed? (FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP)\n"
        "  - If opportunity_type is SCHOLARSHIP/TRAINING, set employment_type=UNKNOWN\n"
        "- experience_level MUST be one of: UNKNOWN, STUDENT, GRADUATE, JUNIOR, MID, SENIOR.\n"
        "  - NEVER use INTERNSHIP as experience_level (that belongs to employment_type/opportunity_type).\n"
        "- Work mode rules:\n"
        "  - If the text clearly says Remote / Work from home, set work_mode=REMOTE.\n"
        "  - If a specific city/country is mentioned (and remote is NOT mentioned), set work_mode=ONSITE.\n"
        "  - If unclear, set work_mode=UNKNOWN.\n"
        "- If a numeric field is not present, set it to null.\n"
        "- For deadline, output YYYY-MM-DD or null.\n"
        "- If present, extract applicant_gender (FEMALE/MALE/ANY/UNKNOWN), employment_subtype (e.g. PERMANENT),\n"
        "  and compensation (amount + currency + period like MONTH).\n"
        "- Keep description_en concise but informative.\n\n"
        f"TAXONOMY_JSON:\n{taxonomy.to_compact_json()}\n\n"
        f"SOURCE_URL:\n{url_text}\n\n"
        f"TEXT_EN:\n{text_en}"
    )


