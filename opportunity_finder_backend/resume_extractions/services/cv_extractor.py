from __future__ import annotations

import json
from typing import Any

from django.utils import timezone

from ai.errors import AITransientError, AIPermanentError
from ai.router import get_provider

from ..models import CVExtractionSession


class CVExtractionService:
    """
    Service for extracting profile information from uploaded CVs using AI.
    """

    def __init__(self):
        self.ai_provider = get_provider()

    def extract_text_from_file(self, file_obj) -> str:
        """
        Extract text content from uploaded CV file.

        Supports PDF and DOCX formats.
        """
        file_name = file_obj.name.lower()

        if file_name.endswith('.pdf'):
            return self._extract_from_pdf(file_obj)
        elif file_name.endswith(('.docx', '.doc')):
            return self._extract_from_docx(file_obj)
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX files.")

    def _extract_from_pdf(self, file_obj) -> str:
        """Extract text from PDF file."""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise AIPermanentError("PDF processing not available. Please install pypdf.")

        text = ""
        reader = PdfReader(file_obj)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    def _extract_from_docx(self, file_obj) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise AIPermanentError("DOCX processing not available. Please install python-docx.")

        doc = Document(file_obj)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()

    def extract_profile_data(self, extracted_text: str, model: str | None = None) -> dict[str, Any]:
        """
        Use AI to extract structured profile data from CV text.
        """
        prompt = self._build_extraction_prompt(extracted_text)
        schema = self._get_extraction_schema()

        try:
            result = self.ai_provider.generate_json(
                prompt=prompt,
                json_schema=schema,
                model=model,
                temperature=0.1,  # Low temperature for consistent extraction
                context="cv_processing",
                user=session.user,
            )

            return result.data or {}

        except AITransientError as e:
            raise e  # Let caller handle retries
        except Exception as e:
            raise AIPermanentError(f"CV extraction failed: {str(e)}")

    def _build_extraction_prompt(self, cv_text: str) -> str:
        """Build the AI prompt for CV extraction."""
        return f"""Extract structured profile information from this CV/resume text.

INSTRUCTIONS:
- Extract factual information only - do not make assumptions
- Leave fields empty if information is not present
- For academic_info, include degree, institution, graduation year, and GPA if available
- For skills, list technical skills, programming languages, tools, etc.
- For experience, include job titles, companies, dates, and brief descriptions
- For languages, include language names and proficiency levels
- For interests, include professional interests or hobbies mentioned

CV TEXT:
{cv_text}

Return the extracted information in the specified JSON format."""

    def _get_extraction_schema(self) -> dict[str, Any]:
        """JSON schema for AI extraction output."""
        return {
            "type": "object",
            "properties": {
                "academic_info": {
                    "type": "object",
                    "properties": {
                        "degrees": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "degree": {"type": "string"},
                                    "institution": {"type": "string"},
                                    "year": {"type": "integer"},
                                    "gpa": {"type": "string"}
                                }
                            }
                        },
                        "certifications": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "skills": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "languages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "language": {"type": "string"},
                            "proficiency": {"type": "string"}
                        }
                    }
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "contact_info": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "location": {"type": "string"}
                    }
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            }
        }

    def process_cv_extraction(self, session: CVExtractionSession) -> None:
        """
        Complete CV extraction workflow for a session.
        """
        try:
            # Extract text from file
            with session.cv_file.open('rb') as f:
                extracted_text = self.extract_text_from_file(f)

            session.extracted_text = extracted_text
            session.status = CVExtractionSession.Status.EXTRACTING
            session.save()

            # Extract structured data with AI
            extracted_data = self.extract_profile_data(extracted_text)

            # Update session with results
            session.academic_info = extracted_data.get("academic_info", {})
            session.skills = extracted_data.get("skills", [])
            session.experience = extracted_data.get("experience", [])
            session.languages = extracted_data.get("languages", [])
            session.interests = extracted_data.get("interests", [])
            session.confidence_score = extracted_data.get("confidence_score")
            session.status = CVExtractionSession.Status.COMPLETED
            session.extracted_at = timezone.now()

            session.save()

        except Exception as e:
            session.status = CVExtractionSession.Status.FAILED
            session.error_message = str(e)
            session.save()
            raise
