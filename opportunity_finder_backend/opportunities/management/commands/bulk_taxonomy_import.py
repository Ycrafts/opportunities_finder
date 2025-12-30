import csv
import json
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from opportunities.models import Domain, Location, OpportunityType, Specialization


class Command(BaseCommand):
    help = "Bulk import/update taxonomy data from CSV or JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to CSV/JSON file to import"
        )
        parser.add_argument(
            "--data",
            type=str,
            help="Inline JSON/CSV data to import"
        )
        parser.add_argument(
            "--type",
            type=str,
            required=True,
            choices=["opportunity_types", "domains", "specializations", "locations"],
            help="Type of taxonomy to import"
        )
        parser.add_argument(
            "--create-only",
            action="store_true",
            help="Only create new records, don't update existing"
        )
        parser.add_argument(
            "--update-only",
            action="store_true",
            help="Only update existing records, don't create new"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes"
        )

    def handle(self, *args, **options):
        if not options["file"] and not options["data"]:
            raise CommandError("Must provide either --file or --data")

        if options["create_only"] and options["update_only"]:
            raise CommandError("Cannot use both --create-only and --update-only")

        # Load data
        if options["file"]:
            try:
                with open(options["file"], 'r', encoding='utf-8') as f:
                    data_content = f.read()
            except FileNotFoundError:
                raise CommandError(f"File not found: {options['file']}")
        else:
            data_content = options["data"]

        # Parse data
        try:
            if data_content.strip().startswith('[') or data_content.strip().startswith('{'):
                # JSON format
                data = json.loads(data_content)
                if isinstance(data, dict):
                    data = [data]
            else:
                # CSV format
                data = self._parse_csv(data_content)
        except (json.JSONDecodeError, Exception) as e:
            raise CommandError(f"Failed to parse data: {e}")

        taxonomy_type = options["type"]
        create_only = options["create_only"]
        update_only = options["update_only"]
        dry_run = options["dry_run"]

        # Process based on type
        if taxonomy_type == "opportunity_types":
            self._import_opportunity_types(data, create_only, update_only, dry_run)
        elif taxonomy_type == "domains":
            self._import_domains(data, create_only, update_only, dry_run)
        elif taxonomy_type == "specializations":
            self._import_specializations(data, create_only, update_only, dry_run)
        elif taxonomy_type == "locations":
            self._import_locations(data, create_only, update_only, dry_run)

    def _parse_csv(self, csv_content):
        """Parse CSV content into list of dicts."""
        reader = csv.DictReader(StringIO(csv_content))
        return list(reader)

    def _import_opportunity_types(self, data, create_only, update_only, dry_run):
        """Import opportunity types."""
        created = 0
        updated = 0
        skipped = 0

        for item in data:
            name = item.get("name", "").strip()
            if not name:
                self.stdout.write(self.style.WARNING(f"Skipping item with empty name: {item}"))
                continue

            try:
                obj, created_flag = OpportunityType.objects.get_or_create(
                    name=name,
                    defaults={}
                )

                if created_flag:
                    if not update_only:
                        if dry_run:
                            self.stdout.write(f"Would create OpportunityType: {name}")
                        else:
                            self.stdout.write(f"Created OpportunityType: {name}")
                        created += 1
                    else:
                        skipped += 1
                else:
                    if not create_only:
                        # Nothing to update for opportunity types currently
                        if dry_run:
                            self.stdout.write(f"Would update OpportunityType: {name}")
                        updated += 1
                    else:
                        skipped += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {name}: {e}"))
                skipped += 1

        self._report_results("OpportunityType", created, updated, skipped, dry_run)

    def _import_domains(self, data, create_only, update_only, dry_run):
        """Import domains."""
        created = 0
        updated = 0
        skipped = 0

        for item in data:
            name = item.get("name", "").strip()
            opportunity_type_name = item.get("opportunity_type", "").strip()

            if not name:
                self.stdout.write(self.style.WARNING(f"Skipping domain with empty name: {item}"))
                continue

            try:
                # Get or create opportunity type
                if opportunity_type_name:
                    opportunity_type, _ = OpportunityType.objects.get_or_create(name=opportunity_type_name)
                else:
                    opportunity_type = None

                obj, created_flag = Domain.objects.get_or_create(
                    name=name,
                    defaults={"opportunity_type": opportunity_type}
                )

                if created_flag:
                    if not update_only:
                        if dry_run:
                            self.stdout.write(f"Would create Domain: {name} (type: {opportunity_type})")
                        else:
                            self.stdout.write(f"Created Domain: {name} (type: {opportunity_type})")
                        created += 1
                    else:
                        skipped += 1
                else:
                    if not create_only:
                        # Update opportunity type if different
                        if obj.opportunity_type != opportunity_type:
                            if dry_run:
                                self.stdout.write(f"Would update Domain: {name} opportunity_type to {opportunity_type}")
                            else:
                                obj.opportunity_type = opportunity_type
                                obj.save()
                                self.stdout.write(f"Updated Domain: {name} opportunity_type to {opportunity_type}")
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing domain {name}: {e}"))
                skipped += 1

        self._report_results("Domain", created, updated, skipped, dry_run)

    def _import_specializations(self, data, create_only, update_only, dry_run):
        """Import specializations."""
        created = 0
        updated = 0
        skipped = 0

        for item in data:
            name = item.get("name", "").strip()
            domain_name = item.get("domain", "").strip()

            if not name:
                self.stdout.write(self.style.WARNING(f"Skipping specialization with empty name: {item}"))
                continue

            try:
                # Get domain
                if domain_name:
                    try:
                        domain = Domain.objects.get(name=domain_name)
                    except Domain.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Domain not found: {domain_name}"))
                        skipped += 1
                        continue
                else:
                    domain = None

                obj, created_flag = Specialization.objects.get_or_create(
                    name=name,
                    defaults={"domain": domain}
                )

                if created_flag:
                    if not update_only:
                        if dry_run:
                            self.stdout.write(f"Would create Specialization: {name} (domain: {domain})")
                        else:
                            self.stdout.write(f"Created Specialization: {name} (domain: {domain})")
                        created += 1
                    else:
                        skipped += 1
                else:
                    if not create_only:
                        # Update domain if different
                        if obj.domain != domain:
                            if dry_run:
                                self.stdout.write(f"Would update Specialization: {name} domain to {domain}")
                            else:
                                obj.domain = domain
                                obj.save()
                                self.stdout.write(f"Updated Specialization: {name} domain to {domain}")
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing specialization {name}: {e}"))
                skipped += 1

        self._report_results("Specialization", created, updated, skipped, dry_run)

    def _import_locations(self, data, create_only, update_only, dry_run):
        """Import locations."""
        created = 0
        updated = 0
        skipped = 0

        for item in data:
            name = item.get("name", "").strip()
            parent_name = item.get("parent", "").strip() if item.get("parent") else None

            if not name:
                self.stdout.write(self.style.WARNING(f"Skipping location with empty name: {item}"))
                continue

            try:
                # Get parent location if specified
                parent = None
                if parent_name:
                    try:
                        parent = Location.objects.get(name=parent_name)
                    except Location.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Parent location not found: {parent_name}"))
                        skipped += 1
                        continue

                obj, created_flag = Location.objects.get_or_create(
                    name=name,
                    defaults={"parent": parent}
                )

                if created_flag:
                    if not update_only:
                        if dry_run:
                            self.stdout.write(f"Would create Location: {name} (parent: {parent})")
                        else:
                            self.stdout.write(f"Created Location: {name} (parent: {parent})")
                        created += 1
                    else:
                        skipped += 1
                else:
                    if not create_only:
                        # Update parent if different
                        if obj.parent != parent:
                            if dry_run:
                                self.stdout.write(f"Would update Location: {name} parent to {parent}")
                            else:
                                obj.parent = parent
                                obj.save()
                                self.stdout.write(f"Updated Location: {name} parent to {parent}")
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing location {name}: {e}"))
                skipped += 1

        self._report_results("Location", created, updated, skipped, dry_run)

    def _report_results(self, model_name, created, updated, skipped, dry_run):
        """Report the results of the import."""
        action = "Would " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{action}{model_name} import complete: {created} created, {updated} updated, {skipped} skipped"
        ))
