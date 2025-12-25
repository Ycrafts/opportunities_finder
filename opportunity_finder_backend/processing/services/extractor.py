from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from datetime import date

from ai.router import get_provider, get_provider_by_name, get_provider_chain_names
from ai.errors import AIConfigurationError, AIError, AIPermanentError, AITransientError
from opportunities.models import Domain, Location, Opportunity, OpportunityType, RawOpportunity, Specialization
from processing.prompts import build_extract_prompt
from processing.schemas import opportunity_extract_schema
from processing.services.dedupe import compute_content_hash
from processing.services.rules import extract_deadline_fast


@dataclass(frozen=True)
class ExtractResult:
    created: bool
    opportunity_id: int


class RawOpportunityExtractor:
    """
    RawOpportunity -> Opportunity extractor using the configured AI provider.
    """

    def _contains_ethiopic(self, text: str) -> bool:
        # Ethiopic block (Amharic, etc.)
        return any("\u1200" <= ch <= "\u137F" for ch in text)

    def _is_probably_english(self, text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return False
        if self._contains_ethiopic(t):
            return False

        alpha = [ch for ch in t if ch.isalpha()]
        if len(alpha) < 20:
            # Too short to be confident; don't assume English.
            return False

        latin = 0
        for ch in alpha:
            o = ord(ch)
            if (65 <= o <= 90) or (97 <= o <= 122):
                latin += 1

        return (latin / max(1, len(alpha))) >= 0.7

    def _save_raw_fields(self, raw: RawOpportunity, *, update_fields: list[str]) -> None:
        # Keep backwards-compat if DB doesn't yet have updated_at (pre-migration local state).
        if "updated_at" in update_fields and not hasattr(raw, "updated_at"):
            update_fields = [f for f in update_fields if f != "updated_at"]
        raw.save(update_fields=update_fields)

    def _provider_chain_for_text(self, text: str) -> list[str]:
        """
        Choose provider order based on the input language characteristics.

        If the chain includes both gemini and groq:
        - Ethiopic/Amharic-heavy: prefer gemini first
        - Mostly-English: prefer groq first
        """
        names = list(get_provider_chain_names() or [])
        if not names:
            return [get_provider().name]

        if "gemini" in names and "groq" in names:
            amharicish = self._contains_ethiopic(text) or (not self._is_probably_english(text))
            preferred = ["gemini", "groq"] if amharicish else ["groq", "gemini"]
            rest = [n for n in names if n not in {"gemini", "groq"}]
            return preferred + rest

        return names

    def _translate_to_english_with_fallback(self, *, raw_text: str, model: str | None):
        chain = self._provider_chain_for_text(raw_text)
        last_transient: Exception | None = None
        first_permanent: Exception | None = None

        for name in chain:
            try:
                provider = get_provider_by_name(name)
                return provider, provider.translate_to_english(text=raw_text, model=model)
            except AITransientError as e:
                last_transient = e
                continue
            except (AIPermanentError, AIConfigurationError) as e:
                if first_permanent is None:
                    first_permanent = e
                continue

        if last_transient is not None:
            raise last_transient
        if first_permanent is not None:
            raise first_permanent
        raise AIError("No AI providers available to translate.")

    def _generate_json_with_fallback(
        self,
        *,
        routing_text: str,
        prompt: str,
        json_schema: dict,
        model: str | None,
        temperature: float,
    ):
        chain = self._provider_chain_for_text(routing_text)
        last_transient: Exception | None = None
        first_permanent: Exception | None = None

        for name in chain:
            try:
                provider = get_provider_by_name(name)
                res = provider.generate_json(
                    prompt=prompt,
                    json_schema=json_schema,
                    temperature=temperature,
                    model=model,
                )
                return provider, res
            except AITransientError as e:
                last_transient = e
                continue
            except (AIPermanentError, AIConfigurationError) as e:
                # Try next provider: another model/provider might produce valid JSON.
                if first_permanent is None:
                    first_permanent = e
                continue

        if last_transient is not None:
            raise last_transient
        if first_permanent is not None:
            raise first_permanent
        raise AIError("No AI providers available to generate JSON.")

    def _extract_with_provider_fallback(
        self,
        *,
        raw_text_for_routing: str,
        text_en: str,
        source_url: str,
        model: str | None,
    ):
        """
        Generate extraction JSON and validate taxonomy; if taxonomy validation fails, try next provider.
        """
        chain = self._provider_chain_for_text(raw_text_for_routing or text_en)
        last_transient: Exception | None = None
        last_transient_provider: str | None = None
        first_permanent: Exception | None = None
        attempts: list[str] = []

        prompt = build_extract_prompt(text_en=text_en, source_url=source_url or "")
        schema = opportunity_extract_schema()

        for name in chain:
            try:
                provider = get_provider_by_name(name)
                ai_res = provider.generate_json(prompt=prompt, json_schema=schema, temperature=0.0, model=model)
                data = ai_res.data or {}
                # Validate taxonomy consistency and load instances; may raise ValueError/AIPermanentError.
                op_type, domain, spec, location = self._validate_taxonomy_ids(data)
                return provider, ai_res, data, op_type, domain, spec, location
            except AITransientError as e:
                last_transient = e
                last_transient_provider = name
                attempts.append(f"{name}: transient: {type(e).__name__}: {str(e)[:200]}")
                continue
            except (AIPermanentError, AIConfigurationError, ValueError) as e:
                attempts.append(f"{name}: permanent: {type(e).__name__}: {str(e)[:200]}")
                if first_permanent is None:
                    first_permanent = e
                continue

        if last_transient is not None:
            summary = " | ".join(attempts) if attempts else "(no attempts recorded)"
            prov = last_transient_provider or "unknown"
            raise AITransientError(
                f"All providers failed extraction. Last transient from {prov}. Attempts: {summary}"
            ) from last_transient
        if first_permanent is not None:
            summary = " | ".join(attempts) if attempts else "(no attempts recorded)"
            raise AIPermanentError(f"All providers failed taxonomy extraction/validation. {summary}") from first_permanent
        raise AIError("No AI providers available to extract and validate taxonomy.")

    def _detect_closed(self, text: str) -> tuple[bool, str]:
        """
        Lightweight "closed/filled" detector.

        We keep this deterministic and independent of the LLM so it works even when extraction is imperfect.
        """
        t = (text or "").lower()
        patterns = [
            "‼️closed‼️",
            "closed",
            "#closed",
            "vacancy filled",
            "position filled",
            "role filled",
            "hiring closed",
            "applications closed",
            "application closed",
            "no longer accepting applications",
            "no longer accepting",
            "we are no longer accepting",
            "this vacancy is closed",
        ]
        for p in patterns:
            if p in t:
                return True, p
        return False, ""

    def _get_remote_location(self) -> Location | None:
        # Convention: a root location named "Remote"
        return Location.objects.filter(name__iexact="Remote", parent__isnull=True).order_by("id").first()

    def _text_mentions_remote(self, text: str) -> bool:
        t = (text or "").lower()
        return any(
            k in t
            for k in [
                "remote",
                "work from home",
                "wfh",
                "home-based",
                "home based",
                "fully remote",
                "remotely",
            ]
        )

    def _cleanup_metadata(self, meta: dict) -> dict:
        """
        Remove noisy/empty legacy extracted fields so metadata stays meaningful.
        """
        m = dict(meta or {})
        extracted = dict(m.get("extracted") or {})
        comp = extracted.get("compensation")
        if isinstance(comp, dict):
            if not any(v is not None and str(v).strip() != "" for v in comp.values()):
                extracted.pop("compensation", None)
        m["extracted"] = extracted
        return m

    def _apply_post_extraction_rules(
        self,
        *,
        opp: Opportunity,
        raw: RawOpportunity,
        text_en: str,
        is_closed: bool,
        closed_match: str,
        location_override: dict | None,
    ) -> None:
        """
        Apply deterministic business rules that should work regardless of whether the Opportunity was
        AI-extracted or deduped from a prior extraction.
        """
        # If work_mode wasn't extracted reliably, infer ONSITE when a concrete location exists
        # and remote keywords are not present.
        if opp.work_mode == Opportunity.WorkMode.UNKNOWN and opp.location_id is not None:
            if not self._text_mentions_remote(raw.raw_text or text_en):
                opp.work_mode = Opportunity.WorkMode.ONSITE

        # Apply closed status mapping
        if is_closed:
            opp.status = Opportunity.Status.ARCHIVED
        else:
            # Auto-expire if deadline is in the past (does not override ARCHIVED).
            if opp.deadline and opp.deadline < timezone.localdate():
                opp.status = Opportunity.Status.EXPIRED

        flags = dict((opp.metadata or {}).get("flags") or {})
        if is_closed:
            flags["closed_detected"] = True
            flags["closed_match"] = closed_match
        if location_override is not None:
            flags["remote_location_override"] = True

        extracted_meta = dict((opp.metadata or {}).get("extracted") or {})
        if location_override is not None:
            extracted_meta["location_override"] = location_override

        opp.metadata = {
            **(opp.metadata or {}),
            "flags": flags,
            "extracted": extracted_meta,
        }
        opp.metadata = self._cleanup_metadata(opp.metadata)

    def _find_prev_extracted_by_hash(self, *, raw: RawOpportunity) -> tuple[RawOpportunity | None, Opportunity | None]:
        """
        Find a previous extracted raw/opportunity by content_hash.

        Includes a small fallback for older rows where content_hash wasn't backfilled yet:
        scan a limited number of recent EXTRACTED raws with empty hash, compute hash in Python,
        and backfill if matched.
        """
        h = (raw.content_hash or "").strip()
        if not h:
            return None, None

        prev_raw = (
            RawOpportunity.objects.filter(
                content_hash=h,
                status=RawOpportunity.ProcessingStatus.EXTRACTED,
            )
            .exclude(id=raw.id)
            .select_related("opportunity")
            .order_by("-id")
            .first()
        )
        if prev_raw and getattr(prev_raw, "opportunity", None):
            # Prefer a canonical extraction (not a dedupe copy), to avoid chaining.
            if not (prev_raw.opportunity.metadata or {}).get("flags", {}).get("dedupe_hit"):
                return prev_raw, prev_raw.opportunity

        # Fallback: backfill older extracted raws with missing content_hash (limited scan)
        candidates = (
            RawOpportunity.objects.filter(status=RawOpportunity.ProcessingStatus.EXTRACTED, content_hash="")
            .exclude(id=raw.id)
            .order_by("-id")[:250]
        )
        for cand in candidates:
            cand_text = (cand.text_en or cand.raw_text or "").strip()
            if not cand_text:
                continue
            cand_hash = compute_content_hash(cand_text)
            if cand_hash and cand_hash == h:
                cand.content_hash = cand_hash
                self._save_raw_fields(cand, update_fields=["content_hash", "updated_at"])
                cand = RawOpportunity.objects.select_related("opportunity").get(id=cand.id)
                if getattr(cand, "opportunity", None):
                    if not (cand.opportunity.metadata or {}).get("flags", {}).get("dedupe_hit"):
                        return cand, cand.opportunity

        # As a last resort, return the most recent match even if it's a dedupe, but keep the root IDs.
        if prev_raw and getattr(prev_raw, "opportunity", None):
            return prev_raw, prev_raw.opportunity
        return None, None

    def _ensure_english_text(self, raw: RawOpportunity, *, model: str | None = None) -> str:
        """
        Returns an English text version for extraction.

        Business rules:
        - If raw.raw_text is already English, we DO NOT translate; we set text_en=raw_text.
        - If we translate, we validate the output is English; otherwise we retry once with a stronger prompt.
        """
        # If we already have a good English translation, use it.
        if raw.text_en and self._is_probably_english(raw.text_en):
            return raw.text_en

        raw_text = (raw.raw_text or "").strip()
        if not raw_text:
            return ""

        # If the raw text is already English, keep it (no AI call).
        if self._is_probably_english(raw_text):
            raw.detected_language = "en"
            raw.text_en = raw_text
            raw.status = RawOpportunity.ProcessingStatus.TRANSLATED
            self._save_raw_fields(raw, update_fields=["detected_language", "text_en", "status", "updated_at"])
            return raw.text_en

        # Not English: translate to English via provider.
        raw.detected_language = "am" if self._contains_ethiopic(raw_text) else (raw.detected_language or "")
        provider, res = self._translate_to_english_with_fallback(raw_text=raw_text, model=model)
        candidate = (res.text or "").strip()

        # If provider returned non-English (or included chatter), retry once with a hard constraint.
        if not self._is_probably_english(candidate):
            retry = provider.generate_text(
                system=(
                    "You are a translation engine.\n"
                    "Output ONLY English translation text.\n"
                    "If the input is already English, output it unchanged.\n"
                    "No labels, no markdown, no extra commentary."
                ),
                prompt=f"Translate this into English:\n\n{raw_text}",
                temperature=0.0,
                model=model,
            )
            candidate = (retry.text or "").strip()

        if not self._is_probably_english(candidate):
            raise ValueError("Translation did not produce English text (refusing to extract from non-English text_en).")

        raw.text_en = candidate
        raw.status = RawOpportunity.ProcessingStatus.TRANSLATED
        self._save_raw_fields(raw, update_fields=["detected_language", "text_en", "status", "updated_at"])
        return raw.text_en

    def _validate_taxonomy_ids(self, data: dict) -> tuple[OpportunityType, Domain, Specialization, Location | None]:
        def _require_int(key: str) -> int:
            val = data.get(key)
            if val is None:
                raise AIPermanentError(f"Extraction missing required field {key} (got null).")
            if isinstance(val, bool):
                # bool is an int subclass; treat as invalid here
                raise AIPermanentError(f"Extraction field {key} must be an integer id (got bool).")
            try:
                return int(val)
            except Exception as e:
                raise AIPermanentError(f"Extraction field {key} must be an integer id (got {val!r}).") from e

        op_type = OpportunityType.objects.get(id=_require_int("op_type_id"))
        domain = Domain.objects.get(id=_require_int("domain_id"))
        spec = Specialization.objects.get(id=_require_int("specialization_id"))

        if domain.opportunity_type_id != op_type.id:
            raise ValueError("Invalid taxonomy: domain does not belong to op_type_id.")
        if spec.domain_id != domain.id:
            raise ValueError("Invalid taxonomy: specialization does not belong to domain_id.")

        loc_id = data.get("location_id")
        location = None
        if loc_id is not None:
            # location_id is optional; but if provided it must be an int-like id
            if isinstance(loc_id, bool):
                raise AIPermanentError("Extraction field location_id must be an integer id (got bool).")
            try:
                location = Location.objects.get(id=int(loc_id))
            except Exception as e:
                raise AIPermanentError(f"Extraction field location_id must be an integer id (got {loc_id!r}).") from e

        return op_type, domain, spec, location

    def extract_one(self, *, raw_id: int, model: str | None = None) -> ExtractResult:
        # IMPORTANT:
        # We keep the extraction flow atomic for consistency, but we MUST persist failure info
        # outside the atomic block. Otherwise, the error status/message gets rolled back and the
        # user sees "failed" with no reason.
        try:
            with transaction.atomic():
                raw = RawOpportunity.objects.select_for_update().get(id=raw_id)

                text_en = self._ensure_english_text(raw, model=model)
                if not text_en.strip():
                    raise ValueError("RawOpportunity has no usable text to extract from.")

                # Compute content hash for dedupe (store it on the raw row).
                # Prefer English text so Amharic + English mixed posts hash consistently after translation.
                raw.content_hash = compute_content_hash(text_en)
                self._save_raw_fields(raw, update_fields=["content_hash", "updated_at"])

                # Dedupe shortcut: if we've already extracted an Opportunity for this content_hash,
                # copy the structured fields instead of calling the LLM again.
                if raw.content_hash:
                    prev_raw, prev_opp = self._find_prev_extracted_by_hash(raw=raw)
                    if prev_raw and prev_opp:

                        # If this raw already has an Opportunity (e.g., task was queued twice),
                        # update it instead of creating a new row (OneToOne raw constraint).
                        opp = getattr(raw, "opportunity", None)
                        created = False
                        if opp is None:
                            opp = Opportunity(raw=raw, title=prev_opp.title)
                            created = True
                        opp.title = prev_opp.title
                        opp.organization = prev_opp.organization
                        opp.description_en = prev_opp.description_en
                        opp.source_url = (raw.source_url or prev_opp.source_url or "").strip()

                        opp.op_type = prev_opp.op_type
                        opp.domain = prev_opp.domain
                        opp.specialization = prev_opp.specialization
                        opp.location = prev_opp.location

                        opp.work_mode = prev_opp.work_mode
                        opp.employment_type = prev_opp.employment_type
                        opp.experience_level = prev_opp.experience_level
                        opp.min_compensation = prev_opp.min_compensation
                        opp.max_compensation = prev_opp.max_compensation
                        # Try to preserve deadline; if missing on the previous extraction (older bug),
                        # fall back to a cheap parser from current text.
                        opp.deadline = prev_opp.deadline or extract_deadline_fast(text_en)
                        opp.published_at = raw.published_at
                        opp.status = prev_opp.status

                        # Mark dedupe in metadata (keep prior ai meta as provenance, but show it's reused)
                        prev_meta = prev_opp.metadata or {}
                        flags = dict(prev_meta.get("flags") or {})
                        flags["dedupe_hit"] = True
                        # Keep stable roots (avoid chaining when prev was already a dedupe copy)
                        flags["deduped_from_raw_id"] = flags.get("deduped_from_raw_id") or prev_raw.id
                        flags["deduped_from_opportunity_id"] = flags.get("deduped_from_opportunity_id") or prev_opp.id

                        opp.metadata = {
                            **prev_meta,
                            "flags": flags,
                        }
                        opp.metadata = self._cleanup_metadata(opp.metadata)

                        # Apply current business rules (closed markers, remote/location overrides, expiry)
                        is_closed, closed_match = self._detect_closed(raw.raw_text or text_en)
                        location_override = None
                        if opp.work_mode == Opportunity.WorkMode.REMOTE:
                            remote_loc = self._get_remote_location()
                            if remote_loc and (opp.location_id != remote_loc.id):
                                location_override = {
                                    "original_location_id": opp.location_id,
                                    "original_location_name": str(opp.location) if opp.location_id else None,
                                    "remote_location_id": remote_loc.id,
                                    "remote_location_name": str(remote_loc),
                                }
                                opp.location = remote_loc
                            elif not remote_loc and opp.location_id is not None:
                                location_override = {
                                    "original_location_id": opp.location_id,
                                    "original_location_name": str(opp.location) if opp.location_id else None,
                                    "remote_location_id": None,
                                    "remote_location_name": None,
                                }
                                opp.location = None

                        self._apply_post_extraction_rules(
                            opp=opp,
                            raw=raw,
                            text_en=text_en,
                            is_closed=is_closed,
                            closed_match=closed_match,
                            location_override=location_override,
                        )

                        opp.full_clean()
                        opp.save()

                        raw.status = RawOpportunity.ProcessingStatus.EXTRACTED
                        raw.error_message = ""
                        self._save_raw_fields(raw, update_fields=["status", "error_message", "updated_at"])

                        return ExtractResult(created=created, opportunity_id=opp.id)

                provider, ai_res, data, op_type, domain, spec, location = self._extract_with_provider_fallback(
                    raw_text_for_routing=(raw.raw_text or ""),
                    text_en=text_en,
                    source_url=(raw.source_url or ""),
                    model=model,
                )

                title = (data.get("title") or "").strip()
                if not title:
                    raise ValueError("Extraction produced empty title.")

                opp = getattr(raw, "opportunity", None)
                created = False
                if opp is None:
                    opp = Opportunity(raw=raw, title=title)
                    created = True

                opp.title = title
                opp.organization = (data.get("organization") or "").strip()
                opp.description_en = (data.get("description_en") or "").strip()
                opp.source_url = (data.get("source_url") or raw.source_url or "").strip()

                opp.op_type = op_type
                opp.domain = domain
                opp.specialization = spec
                opp.location = location

                opp.work_mode = data.get("work_mode") or Opportunity.WorkMode.UNKNOWN
                opp.employment_type = data.get("employment_type") or Opportunity.EmploymentType.UNKNOWN
                opp.experience_level = data.get("experience_level") or Opportunity.ExperienceLevel.UNKNOWN

                opp.min_compensation = data.get("min_compensation")
                opp.max_compensation = data.get("max_compensation")

                # AI outputs ISO date string (YYYY-MM-DD) or null.
                deadline = data.get("deadline")
                if isinstance(deadline, str) and deadline.strip():
                    try:
                        opp.deadline = date.fromisoformat(deadline.strip())
                    except Exception:
                        opp.deadline = None
                else:
                    opp.deadline = None
                if opp.deadline is None:
                    opp.deadline = extract_deadline_fast(text_en)

                # Prefer raw.published_at if present
                opp.published_at = raw.published_at

                # Preserve extraction metadata
                existing_meta = opp.metadata or {}
                ai_meta = {
                    "provider": provider.name,
                    "model": ai_res.model,
                    "confidence": data.get("confidence"),
                    "notes": data.get("notes"),
                }

                # Closed detection based on source text (prefer raw_text, fallback to text_en)
                is_closed, closed_match = self._detect_closed(raw.raw_text or text_en)

                # Remote/location rule (Option A): if remote, set location to "Remote" (if exists), and preserve original.
                location_override = None
                remote_loc = None
                if opp.work_mode == Opportunity.WorkMode.REMOTE:
                    remote_loc = self._get_remote_location()
                    if remote_loc and (opp.location_id != remote_loc.id):
                        location_override = {
                            "original_location_id": opp.location_id,
                            "original_location_name": str(opp.location) if opp.location_id else None,
                            "remote_location_id": remote_loc.id,
                            "remote_location_name": str(remote_loc),
                        }
                        opp.location = remote_loc
                    elif not remote_loc and opp.location_id is not None:
                        # If no dedicated Remote location exists, keep DB consistent by clearing location
                        location_override = {
                            "original_location_id": opp.location_id,
                            "original_location_name": str(opp.location) if opp.location_id else None,
                            "remote_location_id": None,
                            "remote_location_name": None,
                        }
                        opp.location = None

                extracted_meta = dict((existing_meta.get("extracted") or {}))

                # Store optional extracted fields (do not affect DB schema)
                applicant_gender = data.get("applicant_gender")
                if applicant_gender:
                    extracted_meta["applicant_gender"] = applicant_gender

                employment_subtype = data.get("employment_subtype")
                if employment_subtype:
                    extracted_meta["employment_subtype"] = employment_subtype

                compensation = data.get("compensation")
                if isinstance(compensation, dict):
                    # Best-effort cleanup
                    comp_clean = {
                        "amount": compensation.get("amount"),
                        "currency": compensation.get("currency"),
                        "period": compensation.get("period"),
                    }
                    if any(v is not None and str(v).strip() != "" for v in comp_clean.values()):
                        extracted_meta["compensation"] = comp_clean

                opp.metadata = {
                    **existing_meta,
                    "ai": ai_meta,
                    "extracted": extracted_meta,
                }
                opp.metadata = self._cleanup_metadata(opp.metadata)

                # Apply deterministic business rules after metadata is present
                self._apply_post_extraction_rules(
                    opp=opp,
                    raw=raw,
                    text_en=text_en,
                    is_closed=is_closed,
                    closed_match=closed_match,
                    location_override=location_override,
                )

                opp.full_clean()
                opp.save()

                raw.status = RawOpportunity.ProcessingStatus.EXTRACTED
                raw.error_message = ""
                raw.save(update_fields=["status", "error_message"])

                return ExtractResult(created=created, opportunity_id=opp.id)

        except AITransientError as e:
            # Keep retryable raws in the pending set (NEW/TRANSLATED), but persist the error message.
            RawOpportunity.objects.filter(id=raw_id).update(
                error_message=str(e)[:2000],
                updated_at=timezone.now(),
            )
            raise
        except AIPermanentError as e:
            RawOpportunity.objects.filter(id=raw_id).update(
                status=RawOpportunity.ProcessingStatus.FAILED,
                error_message=str(e)[:2000],
                updated_at=timezone.now(),
            )
            raise
        except AIError as e:
            # Unknown AIError type: default to FAILED (safe) but keep the message.
            RawOpportunity.objects.filter(id=raw_id).update(
                status=RawOpportunity.ProcessingStatus.FAILED,
                error_message=str(e)[:2000],
                updated_at=timezone.now(),
            )
            raise
        except Exception as e:
            RawOpportunity.objects.filter(id=raw_id).update(
                status=RawOpportunity.ProcessingStatus.FAILED,
                error_message=str(e)[:2000],
                updated_at=timezone.now(),
            )
            raise


