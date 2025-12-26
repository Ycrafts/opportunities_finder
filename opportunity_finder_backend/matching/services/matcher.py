from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q

from ai.router import get_provider_chain_names
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
                        self._create_match_record(
                            user_profile.user,
                            opportunity,
                            match_result["match_score"],
                            match_result["justification"],
                            match_result.get("stage2_score"),
                        )
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

        Uses user's profile snapshot against opportunity details.
        """
        # This is a placeholder for now - we'll implement the AI logic
        # For now, return a basic match based on Stage 1 success
        return {
            "match_score": 8.0,  # Placeholder
            "justification": "Matches user preferences from Stage 1 filtering",
            "stage2_score": 8.0,
        }

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
