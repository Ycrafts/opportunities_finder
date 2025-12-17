from __future__ import annotations

from django.db import models
from django.utils import timezone


class OpportunityType(models.Model):
    """
    Tier 1 taxonomy (controlled).
    Examples: JOB, SCHOLARSHIP, EVENT, TRAINING, INTERNSHIP
    """

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Domain(models.Model):
    """
    Tier 2 taxonomy (controlled).
    Examples: Software, Finance, Health, Engineering
    """

    opportunity_type = models.ForeignKey(
        OpportunityType, on_delete=models.PROTECT, related_name="domains"
    )
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Specialization(models.Model):
    """
    Tier 3 taxonomy (controlled, constrained by Domain).
    Examples: Backend, Frontend, Accounting, Data Science
    """

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="specializations")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("domain", "name")
        indexes = [
            models.Index(fields=["domain", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.domain.name} / {self.name}"


class Location(models.Model):
    """
    Region > City > Sub-city hierarchy (3-level is the plan).
    """

    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class Meta:
        unique_together = ("parent", "name")
        indexes = [
            models.Index(fields=["parent", "name"]),
        ]

    def __str__(self) -> str:
        parts = [self.name]
        cur = self.parent
        # show up to 2 ancestors for readability (3-level tree)
        while cur:
            parts.append(cur.name)
            cur = cur.parent
        return " / ".join(reversed(parts))

    def descendants(self, include_self: bool = True) -> list["Location"]:
        """
        Dependency-free descendant lookup (OK for 3-level trees).
        """
        result: list[Location] = [self] if include_self else []
        children = list(self.children.all())
        result.extend(children)
        # one more level down (grandchildren)
        for child in children:
            result.extend(list(child.children.all()))
        return result


class JobOpportunity(models.Model):
    """
    Minimal opportunity storage (expanded later by extraction + metadata).
    """

    title = models.CharField(max_length=300)
    description_en = models.TextField(blank=True, default="")
    source_url = models.URLField(max_length=500, blank=True, default="")

    op_type = models.ForeignKey(OpportunityType, on_delete=models.PROTECT, related_name="opportunities")
    domain = models.ForeignKey(Domain, on_delete=models.PROTECT, related_name="opportunities")
    specialization = models.ForeignKey(
        Specialization, on_delete=models.PROTECT, related_name="opportunities"
    )

    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="opportunities")
    is_remote = models.BooleanField(default=False)

    metadata = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        indexes = [
            models.Index(fields=["op_type"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["specialization"]),
            models.Index(fields=["location"]),
            models.Index(fields=["is_remote"]),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self):
        # Ensure taxonomy consistency: Type -> Domain -> Specialization
        if self.domain_id and self.op_type_id and self.domain.opportunity_type_id:
            if self.domain.opportunity_type_id != self.op_type_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"domain": "Selected domain does not belong to the selected opportunity type."}
                )
        if self.specialization_id and self.domain_id:
            if self.specialization.domain_id != self.domain_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"specialization": "Selected specialization does not belong to the selected domain."}
                )
