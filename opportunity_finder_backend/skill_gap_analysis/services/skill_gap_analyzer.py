"""
Skill Gap Analysis Service

Analyzes skill gaps between user profiles and job opportunities,
providing detailed recommendations for skill development.
"""

import json
from typing import Any, Dict, List

from ai.errors import AIError, AITransientError, AIPermanentError
from ai.router import get_provider_chain_names, get_provider_by_name
from opportunities.models import Opportunity
from profiles.models import UserProfile


class SkillGapAnalyzer:
    """
    Analyzes skill gaps between a user profile and job opportunity.

    Uses AI to identify missing skills, proficiency gaps, and provide
    actionable recommendations for career development.
    """

    def __init__(self):
        self.max_analysis_time = 300  # 5 minutes timeout

    def analyze_skill_gaps(
        self,
        user_profile: UserProfile,
        opportunity: Opportunity
    ) -> Dict[str, Any]:
        """
        Perform comprehensive skill gap analysis between user and opportunity.

        Returns structured analysis including:
        - Missing skills with required proficiency levels
        - Current vs required skill levels
        - Recommended learning actions
        - Time estimates and alternative suggestions
        """
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(user_profile, opportunity)

        # Define expected JSON schema
        schema = self._get_analysis_schema()

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
                    temperature=0.2,  # Low temperature for consistent analysis
                    model=None,  # Use provider default
                    context="skill_gap_analysis",
                    user=user_profile.user,
                )

                # Validate and clean the response
                analysis_data = self._clean_analysis_response(result.data)

                return {
                    "missing_skills": analysis_data.get("missing_skills", []),
                    "skill_gaps": analysis_data.get("skill_gaps", {}),
                    "recommended_actions": analysis_data.get("recommended_actions", []),
                    "alternative_suggestions": analysis_data.get("alternative_suggestions", {}),
                    "confidence_score": analysis_data.get("confidence_score", 0.5),
                    "estimated_time_months": analysis_data.get("estimated_time_months"),
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

        # If all providers failed, return basic analysis
        error_msg = "AI analysis failed"
        if last_transient:
            error_msg += f": {last_transient}"
        elif first_permanent:
            error_msg += f": {first_permanent}"

        return {
            "missing_skills": [],
            "skill_gaps": {},
            "recommended_actions": [],
            "alternative_suggestions": {},
            "confidence_score": 0.0,
            "estimated_time_months": None,
            "error": error_msg,
        }

    def _build_analysis_prompt(self, user_profile: UserProfile, opportunity: Opportunity) -> str:
        """Build the AI prompt for skill gap analysis."""

        # Get user profile data
        user_data = user_profile.matching_profile_json or {}
        user_skills = user_data.get("skills", [])
        user_experience = user_data.get("experience", [])
        user_academic = user_data.get("academic_info", {})

        # Build user profile text
        user_parts = []
        user_parts.append(f"Name: {user_data.get('full_name', 'Unknown')}")

        if user_academic:
            academic_parts = []
            if user_academic.get("degree"):
                academic_parts.append(f"Degree: {user_academic['degree']}")
            if user_academic.get("field"):
                academic_parts.append(f"Field: {user_academic['field']}")
            if user_academic.get("institution"):
                academic_parts.append(f"Institution: {user_academic['institution']}")
            if user_academic.get("graduation_year"):
                academic_parts.append(f"Graduation: {user_academic['graduation_year']}")
            if academic_parts:
                user_parts.append(f"Education: {' | '.join(academic_parts)}")

        if user_skills:
            user_parts.append(f"Skills: {', '.join(user_skills)}")

        if user_experience:
            exp_parts = []
            for exp in user_experience[:3]:  # Limit to recent 3 experiences
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    duration = exp.get("duration", "")
                    if title or company:
                        exp_parts.append(f"{title} at {company} ({duration})")
                elif isinstance(exp, str):
                    exp_parts.append(exp)
            if exp_parts:
                user_parts.append(f"Experience: {'; '.join(exp_parts)}")

        user_profile_text = "\n".join(user_parts)

        # Build opportunity requirements
        opp_parts = []
        opp_parts.append(f"Job Title: {opportunity.title or 'Unknown'}")
        opp_parts.append(f"Organization: {opportunity.organization or 'Unknown'}")

        if opportunity.description_en:
            opp_parts.append(f"Job Description:\n{opportunity.description_en}")

        if opportunity.experience_level:
            opp_parts.append(f"Required Experience Level: {opportunity.experience_level}")

        if opportunity.employment_type:
            opp_parts.append(f"Employment Type: {opportunity.employment_type}")

        opportunity_text = "\n".join(opp_parts)

        prompt = f"""
You are an expert career counselor specializing in skill gap analysis for job matching.

USER PROFILE:
{user_profile_text}

JOB OPPORTUNITY:
{opportunity_text}

TASK:
Perform a detailed skill gap analysis comparing the user's current qualifications against this job opportunity's requirements.

ANALYSIS REQUIREMENTS (keep it concise):

1. **Missing Skills**: List the top 5 most important missing skills.
2. **Skill Gaps**: For the top 5 highest-priority skills only (including any missing ones), assess:
   - User's current proficiency level (Beginner/Intermediate/Advanced/Expert)
   - Required proficiency level for this job
   - Gap assessment (None/Small/Medium/Large)
3. **Recommended Actions**: Provide up to 5 specific, actionable learning recommendations:
   - Online courses (Coursera, Udemy, edX)
   - Certifications to pursue
   - Projects to build
   - Books/resources to study
   - Timeline estimates
4. **Time Estimate**: Estimate months needed to bridge major gaps
5. **Alternative Suggestions**: If gaps are very large, suggest:
   - Entry-level positions to start with
   - Related roles that better match current skills
   - Additional qualifications needed

ANALYSIS GUIDELINES:
- Be specific and actionable in recommendations
- Consider both technical skills and soft skills
- Factor in user's current experience level
- Provide realistic time estimates
- Focus on high-impact skills for this specific role
- Rate confidence in your analysis (0.0-1.0)

Return analysis as structured JSON with the following format (keep arrays short, max 5 items):
{{
  "missing_skills": ["skill1", "skill2", ...],
  "skill_gaps": {{
    "skill_name": {{
      "current_level": "Beginner|Intermediate|Advanced|Expert",
      "required_level": "Beginner|Intermediate|Advanced|Expert",
      "gap_size": "None|Small|Medium|Large",
      "priority": "High|Medium|Low"
    }},
    ...
  }},
  "recommended_actions": [
    {{
      "skill": "skill_name",
      "action_type": "Course|Certification|Project|Practice",
      "description": "Specific recommendation",
      "resource": "Platform/course name",
      "estimated_time_weeks": 4,
      "cost": "Free|Low|Medium|High",
      "priority": "High|Medium|Low"
    }},
    ...
  ],
  "estimated_time_months": 6,
  "alternative_suggestions": {{
    "entry_level_roles": ["role1", "role2"],
    "bridging_positions": ["position1", "position2"],
    "additional_qualifications": ["cert1", "degree2"]
  }},
  "confidence_score": 0.85
}}
"""

        return prompt.strip()

    def _get_analysis_schema(self) -> Dict[str, Any]:
        """Define the JSON schema for AI analysis response."""
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["missing_skills", "skill_gaps", "recommended_actions", "confidence_score"],
            "properties": {
                "missing_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills the user completely lacks"
                },
                "skill_gaps": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "current_level": {
                                    "type": "string",
                                    "enum": ["Beginner", "Intermediate", "Advanced", "Expert"]
                                },
                                "required_level": {
                                    "type": "string",
                                    "enum": ["Beginner", "Intermediate", "Advanced", "Expert"]
                                },
                                "gap_size": {
                                    "type": "string",
                                    "enum": ["None", "Small", "Medium", "Large"]
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["High", "Medium", "Low"]
                                }
                            },
                            "required": ["current_level", "required_level", "gap_size"]
                        }
                    },
                    "description": "Detailed skill gap assessment"
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill": {"type": "string"},
                            "action_type": {
                                "type": "string",
                                "enum": ["Course", "Certification", "Project", "Practice", "Reading"]
                            },
                            "description": {"type": "string"},
                            "resource": {"type": "string"},
                            "estimated_time_weeks": {"type": "integer", "minimum": 1},
                            "cost": {
                                "type": "string",
                                "enum": ["Free", "Low", "Medium", "High"]
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["High", "Medium", "Low"]
                            }
                        },
                        "required": ["skill", "action_type", "description"]
                    },
                    "description": "Recommended learning actions"
                },
                "estimated_time_months": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 24,
                    "description": "Estimated months to bridge major gaps"
                },
                "alternative_suggestions": {
                    "type": "object",
                    "properties": {
                        "entry_level_roles": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "bridging_positions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "additional_qualifications": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "AI confidence in the analysis"
                }
            }
        }

    def _clean_analysis_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate the AI response data."""
        cleaned = {}

        # Ensure missing_skills is a list
        cleaned["missing_skills"] = data.get("missing_skills", [])
        if not isinstance(cleaned["missing_skills"], list):
            cleaned["missing_skills"] = []
        cleaned["missing_skills"] = cleaned["missing_skills"][:5]

        # Ensure skill_gaps is a dict with proper structure
        skill_gaps = data.get("skill_gaps", {})
        if isinstance(skill_gaps, dict):
            cleaned_skill_gaps = {}
            for skill_name, gap_info in list(skill_gaps.items())[:5]:
                if isinstance(gap_info, dict):
                    cleaned_skill_gaps[skill_name] = {
                        "current_level": gap_info.get("current_level", "Beginner"),
                        "required_level": gap_info.get("required_level", "Intermediate"),
                        "gap_size": gap_info.get("gap_size", "Medium"),
                        "priority": gap_info.get("priority", "Medium")
                    }
            cleaned["skill_gaps"] = cleaned_skill_gaps
        else:
            cleaned["skill_gaps"] = {}

        # Ensure recommended_actions is a list
        recommended_actions = data.get("recommended_actions", [])
        if isinstance(recommended_actions, list):
            cleaned_actions = []
            for action in recommended_actions[:5]:
                if isinstance(action, dict):
                    cleaned_actions.append({
                        "skill": action.get("skill", ""),
                        "action_type": action.get("action_type", "Course"),
                        "description": action.get("description", ""),
                        "resource": action.get("resource", ""),
                        "estimated_time_weeks": int(action.get("estimated_time_weeks", 4)),
                        "cost": action.get("cost", "Free"),
                        "priority": action.get("priority", "Medium")
                    })
            cleaned["recommended_actions"] = cleaned_actions
        else:
            cleaned["recommended_actions"] = []

        # Ensure alternative_suggestions is a dict
        alt_suggestions = data.get("alternative_suggestions", {})
        if isinstance(alt_suggestions, dict):
            cleaned["alternative_suggestions"] = {
                "entry_level_roles": alt_suggestions.get("entry_level_roles", []),
                "bridging_positions": alt_suggestions.get("bridging_positions", []),
                "additional_qualifications": alt_suggestions.get("additional_qualifications", [])
            }
        else:
            cleaned["alternative_suggestions"] = {
                "entry_level_roles": [],
                "bridging_positions": [],
                "additional_qualifications": []
            }

        # Ensure confidence_score is a float between 0 and 1
        confidence = data.get("confidence_score", 0.5)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5
        cleaned["confidence_score"] = confidence

        # Ensure estimated_time_months is reasonable
        time_estimate = data.get("estimated_time_months")
        if isinstance(time_estimate, int) and 1 <= time_estimate <= 24:
            cleaned["estimated_time_months"] = time_estimate
        else:
            cleaned["estimated_time_months"] = None

        return cleaned
