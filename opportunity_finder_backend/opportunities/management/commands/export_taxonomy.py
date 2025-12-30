import csv
import json
import sys
from io import StringIO

from django.core.management.base import BaseCommand

from opportunities.models import Domain, Location, OpportunityType, Specialization


class Command(BaseCommand):
    help = "Export taxonomy data to JSON or CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=["opportunity_types", "domains", "specializations", "locations", "all"],
            default="all",
            help="Type of taxonomy to export"
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["json", "csv"],
            default="json",
            help="Output format"
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path (defaults to stdout)"
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON indentation level"
        )

    def handle(self, *args, **options):
        taxonomy_type = options["type"]
        output_format = options["format"]
        output_file = options["output"]
        indent = options["indent"]

        # Collect data
        data = {}

        if taxonomy_type in ["opportunity_types", "all"]:
            data["opportunity_types"] = [
                {"name": obj.name}
                for obj in OpportunityType.objects.order_by("name")
            ]

        if taxonomy_type in ["domains", "all"]:
            data["domains"] = [
                {
                    "name": obj.name,
                    "opportunity_type": obj.opportunity_type.name if obj.opportunity_type else None
                }
                for obj in Domain.objects.select_related("opportunity_type").order_by("name")
            ]

        if taxonomy_type in ["specializations", "all"]:
            data["specializations"] = [
                {
                    "name": obj.name,
                    "domain": obj.domain.name if obj.domain else None,
                    "opportunity_type": obj.domain.opportunity_type.name if obj.domain and obj.domain.opportunity_type else None
                }
                for obj in Specialization.objects.select_related("domain__opportunity_type").order_by("name")
            ]

        if taxonomy_type in ["locations", "all"]:
            data["locations"] = [
                {
                    "name": obj.name,
                    "parent": obj.parent.name if obj.parent else None
                }
                for obj in Location.objects.select_related("parent").order_by("name")
            ]

        # Output data
        if output_format == "json":
            output_content = json.dumps(data, indent=indent, ensure_ascii=False)
        else:  # CSV format
            if taxonomy_type == "all":
                self.stdout.write(self.style.ERROR("CSV format not supported for 'all' types. Use JSON or specify a single type."))
                return
            output_content = self._format_as_csv(data[taxonomy_type], taxonomy_type.rstrip('s'))

        # Write output
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content)
            self.stdout.write(self.style.SUCCESS(f"Exported to {output_file}"))
        else:
            self.stdout.write(output_content)

    def _format_as_csv(self, data, type_name):
        """Format data as CSV."""
        if not data:
            return ""

        # Get all possible keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())

        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()
