from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q

from ai.errors import AIError, AITransientError, AIPermanentError
from ai.router import get_provider_by_name, get_provider_chain_names
from configs.models import MatchConfig
from opportunities.models import Opportunity
from profiles.models import UserProfile

from ..models import Match


class OpportunityMatcher:
    """
    Core matching service: finds relevant opportunities for users using two-stage approach.

    Stage 1: SQL pre-filter (fast, eliminates 90%+ candidates)
    Stage 2: AI re-ranking (precise, but expensive - limited to top candidates)
    """

    def __init__(self, *, max_stage1_candidates: int = 20, min_match_score: float = 7.0):
        """
        Args:
            max_stage1_candidates: Maximum opportunities to pass to Stage 2 AI (cost control)
            min_match_score: Minimum score to create a Match record
        """
        self.max_stage1_candidates = max_stage1_candidates
        self.min_match_score = min_match_score

    def match_opportunity_to_users(
        self, *, opportunity_id: int, user_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """
        Match a single opportunity against users (or specified user subset).

        This is called when a new opportunity is extracted and becomes available.
        """
        try:
            opportunity = Opportunity.objects.select_related(
                "op_type", "domain", "specialization", "location"
            ).get(id=opportunity_id, status=Opportunity.Status.ACTIVE)
        except Opportunity.DoesNotExist:
            return {"error": f"Opportunity {opportunity_id} not found or not active"}

        # Get active users with profiles and configs
        users_query = UserProfile.objects.select_related(
            "user", "user__match_config"
        ).filter(
            user__is_active=True,
            # Only users with matching profiles (CV parsed)
            matching_profile_json__isnull=False,
        )

        if user_ids:
            users_query = users_query.filter(user_id__in=user_ids)

        users = list(users_query)
        total_users = len(users)

        if not users:
            return {"matched_users": 0, "total_users": total_users, "matches_created": 0}

        matches_created = 0

        for user_profile in users:
            try:
                match_result = self._match_single_user(opportunity, user_profile)
                if match_result and match_result["match_score"] >= self.min_match_score:
                    # Only create/update record if this is a new match (not reusing existing)
                    if not match_result.get("existing_match"):
                        match_record = self._create_match_record(
                            user_profile.user,
                            opportunity,
                            match_result["match_score"],
                            match_result["justification"],
                            match_result.get("stage2_score"),
                        )
                        # Trigger notification creation for new matches
                        self._trigger_notifications(match_record)
                    matches_created += 1
            except Exception as e:
                # Log error but continue with other users
                print(f"Error matching opportunity {opportunity_id} to user {user_profile.user_id}: {e}")
                continue

        return {
            "opportunity_id": opportunity_id,
            "matched_users": matches_created,
            "total_users": total_users,
            "matches_created": matches_created,
        }

    def _match_single_user(
        self, opportunity: Opportunity, user_profile: UserProfile
    ) -> dict[str, Any] | None:
        """
        Match a single opportunity against a single user.

        Returns match result dict or None if no match.
        """
        # Get user's match config (preferences)
        config = getattr(user_profile.user, "match_config", None)
        if not config:
            return None

        # Check if match already exists (avoid redundant AI calls)
        existing_match = Match.objects.filter(
            user=user_profile.user,
            opportunity=opportunity
        ).first()

        if existing_match:
            # Return existing match result without running AI again
            return {
                "match_score": existing_match.match_score,
                "justification": existing_match.justification,
                "stage2_score": existing_match.stage2_score,
                "existing_match": True,
            }

        # Stage 1: SQL pre-filter based on user preferences
        stage1_candidates = self._stage1_sql_filter(opportunity, config)

        if not stage1_candidates:
            # No match at Stage 1 level
            return {"match_score": 0.0, "justification": "Does not match user preferences"}

        # Stage 2: AI re-ranking (only if we have candidates and AI is available)
        if len(stage1_candidates) <= self.max_stage1_candidates:
            return self._stage2_ai_rerank(opportunity, user_profile, stage1_candidates)
        else:
            # Too many candidates, skip AI (cost control)
            return {
                "match_score": 5.0,  # Neutral score
                "justification": "Matches basic preferences but too many candidates for detailed analysis"
            }

    def _trigger_notifications(self, match) -> None:
        """
        Trigger notification creation for a new match.

        Uses Celery to create and send notifications asynchronously.
        """
        from notifications.tasks import create_notifications_for_match

        # Queue notification creation task
        create_notifications_for_match.delay(match.id)

    def _stage1_sql_filter(self, opportunity: Opportunity, config: MatchConfig) -> list[Opportunity]:
        """
        Stage 1: Fast SQL filtering based on user preferences.

        This eliminates 90%+ of irrelevant opportunities before expensive AI processing.
        """
        # Build Q objects for filtering
        filters = Q(status=Opportunity.Status.ACTIVE)

        # Opportunity Type preferences
        if config.preferred_opportunity_types.exists():
            preferred_types = list(config.preferred_opportunity_types.values_list("id", flat=True))
            filters &= Q(op_type_id__in=preferred_types)
        elif config.muted_opportunity_types.exists():
            muted_types = list(config.muted_opportunity_types.values_list("id", flat=True))
            filters &= ~Q(op_type_id__in=muted_types)

        # Domain preferences
        if config.preferred_domains.exists():
            preferred_domains = list(config.preferred_domains.values_list("id", flat=True))
            filters &= Q(domain_id__in=preferred_domains)

        # Specialization preferences
        if config.preferred_specializations.exists():
            preferred_specs = list(config.preferred_specializations.values_list("id", flat=True))
            filters &= Q(specialization_id__in=preferred_specs)

        # Location preferences (with hierarchy support)
        if config.preferred_locations.exists():
            preferred_location_ids = set()
            for location in config.preferred_locations.all():
                # Include location and all its descendants (city + sub-cities)
                preferred_location_ids.update(location.descendants(include_self=True))

            filters &= Q(location_id__in=preferred_location_ids)

        # Work mode preferences
        if config.work_mode != MatchConfig.WorkMode.ANY:
            if config.work_mode == MatchConfig.WorkMode.REMOTE:
                filters &= Q(work_mode=Opportunity.WorkMode.REMOTE)
            elif config.work_mode == MatchConfig.WorkMode.ONSITE:
                filters &= Q(work_mode=Opportunity.WorkMode.ONSITE)
            elif config.work_mode == MatchConfig.WorkMode.HYBRID:
                filters &= Q(work_mode=Opportunity.WorkMode.HYBRID)

        # Employment type preferences
        if config.employment_type != MatchConfig.EmploymentType.ANY:
            if config.employment_type == MatchConfig.EmploymentType.FULL_TIME:
                filters &= Q(employment_type=Opportunity.EmploymentType.FULL_TIME)
            elif config.employment_type == MatchConfig.EmploymentType.PART_TIME:
                filters &= Q(employment_type=Opportunity.EmploymentType.PART_TIME)
            elif config.employment_type == MatchConfig.EmploymentType.CONTRACT:
                filters &= Q(employment_type=Opportunity.EmploymentType.CONTRACT)
            elif config.employment_type == MatchConfig.EmploymentType.INTERNSHIP:
                filters &= Q(employment_type=Opportunity.EmploymentType.INTERNSHIP)

        # Experience level preferences
        if config.experience_level != MatchConfig.ExperienceLevel.ANY:
            if config.experience_level == MatchConfig.ExperienceLevel.STUDENT:
                filters &= Q(experience_level=Opportunity.ExperienceLevel.STUDENT)
            elif config.experience_level == MatchConfig.ExperienceLevel.GRADUATE:
                filters &= Q(experience_level=Opportunity.ExperienceLevel.GRADUATE)
            elif config.experience_level == MatchConfig.ExperienceLevel.JUNIOR:
                filters &= Q(experience_level=Opportunity.ExperienceLevel.JUNIOR)
            elif config.experience_level == MatchConfig.ExperienceLevel.MID:
                filters &= Q(experience_level=Opportunity.ExperienceLevel.MID)
            elif config.experience_level == MatchConfig.ExperienceLevel.SENIOR:
                filters &= Q(experience_level=Opportunity.ExperienceLevel.SENIOR)

        # Compensation preferences (salary range)
        if config.min_compensation is not None:
            filters &= Q(max_compensation__gte=config.min_compensation)
        if config.max_compensation is not None:
            filters &= Q(min_compensation__lte=config.max_compensation)

        # Deadline window preferences
        if config.deadline_after:
            filters &= Q(deadline__gte=config.deadline_after)
        if config.deadline_before:
            filters &= Q(deadline__lte=config.deadline_before)

        # Execute query - limit to reasonable number for Stage 2
        candidates = list(
            Opportunity.objects.filter(filters).order_by("-published_at")[:self.max_stage1_candidates]
        )

        return candidates

    def _stage2_ai_rerank(
        self, opportunity: Opportunity, user_profile: UserProfile, stage1_candidates: list[Opportunity]
    ) -> dict[str, Any]:
        """
        Stage 2: AI-powered re-ranking using semantic matching.

        Uses user's profile snapshot against opportunity details for intelligent scoring.
        """
        from ai.errors import AIError, AITransientError, AIPermanentError
        from ai.router import get_provider_chain_names, get_provider_by_name

        # Build the AI prompt
        prompt = self._build_matching_prompt(opportunity, user_profile)

        # JSON schema for structured AI response
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["relevance_score", "justification"],
            "properties": {
                "relevance_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 10.0,
                    "description": "How relevant this opportunity is to the user (0-10 scale)"
                },
                "justification": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Brief explanation of why this score was given"
                }
            }
        }

        # Try AI providers with fallback
        chain = get_provider_chain_names()
        last_transient: Exception | None = None
        first_permanent: Exception | None = None

        for provider_name in chain:
            try:
                provider = get_provider_by_name(provider_name)
                result = provider.generate_json(
                    prompt=prompt,
                    json_schema=schema,
                    temperature=0.3,  # Low temperature for consistent scoring
                    model=None,  # Use provider default
                    context="matching",
                    user=user_profile.user,
                )

                # Validate the response
                score = result.data.get("relevance_score", 0.0)
                justification = result.data.get("justification", "")

                # Ensure score is in valid range
                score = max(0.0, min(10.0, float(score)))

                return {
                    "match_score": score,
                    "justification": str(justification)[:500],  # Truncate if too long
                    "stage2_score": score,
                    "ai_provider": provider_name,
                    "ai_model": result.model,
                }

            except AITransientError as e:
                last_transient = e
                continue
            except (AIPermanentError, Exception) as e:
                if first_permanent is None:
                    first_permanent = e
                continue

        # If all providers failed, fall back to a basic score
        error_msg = "AI matching failed"
        if last_transient:
            error_msg += f": {last_transient}"
        elif first_permanent:
            error_msg += f": {first_permanent}"

        return {
            "match_score": 5.0,  # Neutral fallback score
            "justification": f"Unable to perform AI matching - {error_msg}",
            "stage2_score": None,  # Indicate AI failure
        }

    def _build_matching_prompt(self, opportunity: Opportunity, user_profile: UserProfile) -> str:
        """Build the AI prompt for matching user profile against opportunity."""

        # Get user profile text
        user_text = user_profile.matching_profile_text
        if not user_text:
            user_text = "No profile information available"

        # Build opportunity description
        opp_parts = []
        if opportunity.title:
            opp_parts.append(f"Title: {opportunity.title}")
        if opportunity.organization:
            opp_parts.append(f"Organization: {opportunity.organization}")
        if opportunity.description_en:
            opp_parts.append(f"Description: {opportunity.description_en}")
        if opportunity.work_mode:
            opp_parts.append(f"Work Mode: {opportunity.work_mode}")
        if opportunity.employment_type:
            opp_parts.append(f"Employment Type: {opportunity.employment_type}")
        if opportunity.experience_level:
            opp_parts.append(f"Experience Level: {opportunity.experience_level}")
        if opportunity.min_compensation or opportunity.max_compensation:
            comp_range = []
            if opportunity.min_compensation:
                comp_range.append(f"min: {opportunity.min_compensation}")
            if opportunity.max_compensation:
                comp_range.append(f"max: {opportunity.max_compensation}")
            opp_parts.append(f"Compensation: {', '.join(comp_range)}")

        opportunity_text = "\n".join(opp_parts)

        prompt = f"""
You are an expert career counselor matching job opportunities to candidates.

USER PROFILE:
{user_text}

OPPORTUNITY DETAILS:
{opportunity_text}

TASK:
Analyze how well this opportunity matches the user's profile, skills, experience, and career interests.

Consider:
- Skill alignment and relevance
- Experience level match
- Career progression potential
- Interest alignment
- Work mode preferences
- Compensation expectations

Provide a relevance score from 0-10 (where 10 is perfect match) and a brief justification.

Score Guidelines:
- 9-10: Exceptional match, highly relevant skills/experience
- 7-8: Good match with some relevant experience
- 5-6: Moderate match, some alignment
- 3-4: Weak match, limited relevance
- 0-2: Poor match, not suitable

Return your analysis as JSON with 'relevance_score' and 'justification' fields.
"""

        return prompt.strip()

    @transaction.atomic
    def _create_match_record(
        self,
        user,
        opportunity: Opportunity,
        match_score: float,
        justification: str,
        stage2_score: float | None = None,
    ) -> Match:
        """
        Create or update a Match record for user-opportunity pair.
        """
        match, created = Match.objects.update_or_create(
            user=user,
            opportunity=opportunity,
            defaults={
                "match_score": match_score,
                "justification": justification,
                "stage2_score": stage2_score,
                "stage1_passed": True,
                "status": Match.MatchStatus.ACTIVE,
            }
        )
        return match
