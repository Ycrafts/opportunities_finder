from django.core.management.base import BaseCommand

from opportunities.models import Opportunity
from profiles.models import UserProfile

from ...services.matcher import OpportunityMatcher


class Command(BaseCommand):
    help = "Match opportunities against users for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--opportunity-id",
            type=int,
            help="Specific opportunity ID to match"
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Specific user ID to match against"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum opportunities to process"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be matched without creating records"
        )

    def handle(self, *args, **options):
        matcher = OpportunityMatcher()

        if options["opportunity_id"]:
            # Match specific opportunity
            self.stdout.write(f"Matching opportunity {options['opportunity_id']}...")
            result = matcher.match_opportunity_to_users(
                opportunity_id=options["opportunity_id"],
                user_ids=[options["user_id"]] if options["user_id"] else None
            )
            self.stdout.write(self.style.SUCCESS(f"Result: {result}"))

        else:
            # Match recent opportunities
            opportunities = Opportunity.objects.filter(
                status=Opportunity.Status.ACTIVE
            ).order_by("-created_at")[:options["limit"]]

            self.stdout.write(f"Matching {len(opportunities)} recent opportunities...")

            total_matches = 0
            for opp in opportunities:
                if options["dry_run"]:
                    self.stdout.write(f"Would match opportunity: {opp.title}")
                    continue

                result = matcher.match_opportunity_to_users(
                    opportunity_id=opp.id,
                    user_ids=[options["user_id"]] if options["user_id"] else None
                )
                matches_created = result.get("matches_created", 0)
                total_matches += matches_created
                self.stdout.write(f"  {opp.title}: {matches_created} matches")

            self.stdout.write(self.style.SUCCESS(f"Total matches created: {total_matches}"))
