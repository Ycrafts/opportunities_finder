from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Count

from opportunities.models import Domain, Location, OpportunityType, Specialization


class Command(BaseCommand):
    help = "Analyze taxonomy health and relationships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-orphans",
            action="store_true",
            help="Automatically fix orphaned relationships"
        )
        parser.add_argument(
            "--report-only",
            action="store_true",
            help="Only show report, don't fix anything"
        )

    def handle(self, *args, **options):
        fix_orphans = options["fix_orphans"]
        report_only = options["report_only"]

        self.stdout.write(self.style.SUCCESS("=== Taxonomy Health Report ===\n"))

        # Check opportunity types
        self._check_opportunity_types()

        # Check domains
        self._check_domains()

        # Check specializations
        self._check_specializations()

        # Check locations
        self._check_locations()

        # Check usage statistics
        self._check_usage_stats()

        # Fix orphans if requested
        if fix_orphans and not report_only:
            self._fix_orphans()

    def _check_opportunity_types(self):
        """Check opportunity types."""
        total = OpportunityType.objects.count()
        self.stdout.write(f"Opportunity Types: {total}")

        # Domains per opportunity type
        op_type_stats = (
            Domain.objects.values("opportunity_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        if op_type_stats:
            self.stdout.write("  Domains per Opportunity Type:")
            for stat in op_type_stats:
                name = stat["opportunity_type__name"] or "None"
                self.stdout.write(f"    {name}: {stat['count']} domains")
        self.stdout.write("")

    def _check_domains(self):
        """Check domains and their relationships."""
        total = Domain.objects.count()
        with_op_type = Domain.objects.filter(opportunity_type__isnull=False).count()
        without_op_type = Domain.objects.filter(opportunity_type__isnull=True).count()

        self.stdout.write(f"Domains: {total}")
        self.stdout.write(f"  With opportunity type: {with_op_type}")
        self.stdout.write(f"  Without opportunity type: {without_op_type}")

        if without_op_type > 0:
            self.stdout.write("  Domains without opportunity type:")
            for domain in Domain.objects.filter(opportunity_type__isnull=True):
                self.stdout.write(f"    - {domain.name}")
        self.stdout.write("")

    def _check_specializations(self):
        """Check specializations and their relationships."""
        total = Specialization.objects.count()
        with_domain = Specialization.objects.filter(domain__isnull=False).count()
        without_domain = Specialization.objects.filter(domain__isnull=True).count()

        self.stdout.write(f"Specializations: {total}")
        self.stdout.write(f"  With domain: {with_domain}")
        self.stdout.write(f"  Without domain: {without_domain}")

        if without_domain > 0:
            self.stdout.write("  Specializations without domain:")
            for spec in Specialization.objects.filter(domain__isnull=True):
                self.stdout.write(f"    - {spec.name}")

        # Specializations per domain
        domain_stats = (
            Specialization.objects.values("domain__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        if domain_stats:
            self.stdout.write("  Specializations per Domain:")
            for stat in domain_stats:
                name = stat["domain__name"] or "None"
                self.stdout.write(f"    {name}: {stat['count']} specializations")
        self.stdout.write("")

    def _check_locations(self):
        """Check locations and hierarchy."""
        total = Location.objects.count()
        root_locations = Location.objects.filter(parent__isnull=True).count()
        child_locations = Location.objects.filter(parent__isnull=False).count()

        self.stdout.write(f"Locations: {total}")
        self.stdout.write(f"  Root locations: {root_locations}")
        self.stdout.write(f"  Child locations: {child_locations}")

        # Hierarchy depth analysis
        self._analyze_location_hierarchy()
        self.stdout.write("")

    def _analyze_location_hierarchy(self):
        """Analyze location hierarchy depth."""
        max_depth = 0
        location_tree = defaultdict(list)

        # Build parent-child relationships
        for location in Location.objects.select_related("parent"):
            if location.parent:
                location_tree[location.parent.name].append(location.name)

        # Calculate depths
        def get_depth(name, visited=None):
            if visited is None:
                visited = set()
            if name in visited:
                return 0  # Circular reference protection
            visited.add(name)

            if name not in location_tree:
                return 0

            child_depths = [get_depth(child, visited.copy()) for child in location_tree[name]]
            return 1 + max(child_depths) if child_depths else 0

        root_locations = Location.objects.filter(parent__isnull=True)
        for root in root_locations:
            depth = get_depth(root.name)
            max_depth = max(max_depth, depth)

        self.stdout.write(f"  Maximum hierarchy depth: {max_depth}")

        # Show hierarchy issues
        orphans = []
        for location in Location.objects.filter(parent__isnull=False):
            if not Location.objects.filter(name=location.parent.name).exists():
                orphans.append(location.name)

        if orphans:
            self.stdout.write(f"  Locations with invalid parents: {len(orphans)}")
            for orphan in orphans[:5]:  # Show first 5
                self.stdout.write(f"    - {orphan}")
            if len(orphans) > 5:
                self.stdout.write(f"    ... and {len(orphans) - 5} more")

    def _check_usage_stats(self):
        """Check how taxonomy is being used."""
        self.stdout.write("Usage Statistics:")

        # Most used opportunity types
        from opportunities.models import Opportunity
        op_type_usage = (
            Opportunity.objects.values("op_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        if op_type_usage:
            self.stdout.write("  Most used Opportunity Types:")
            for stat in op_type_usage:
                name = stat["op_type__name"] or "None"
                self.stdout.write(f"    {name}: {stat['count']} opportunities")

        # Most used domains
        domain_usage = (
            Opportunity.objects.values("domain__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        if domain_usage:
            self.stdout.write("  Most used Domains:")
            for stat in domain_usage:
                name = stat["domain__name"] or "None"
                self.stdout.write(f"    {name}: {stat['count']} opportunities")

    def _fix_orphans(self):
        """Fix orphaned relationships."""
        self.stdout.write(self.style.SUCCESS("\n=== Fixing Orphaned Relationships ==="))

        # Could implement automatic fixes here, but for now just report
        self.stdout.write("Automatic fixing not yet implemented. Use manual admin interface.")
