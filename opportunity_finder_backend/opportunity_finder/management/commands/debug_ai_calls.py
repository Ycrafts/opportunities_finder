from django.core.management.base import BaseCommand
from opportunities.models import RawOpportunity, Opportunity
from ai_usage.models import AIAPICall
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Debug AI call patterns and pending opportunities"

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING AI CALL PATTERNS ===\n")

        # Check raw opportunities
        self.stdout.write("RawOpportunities by status:")
        total_raw = RawOpportunity.objects.count()
        for status, _ in RawOpportunity.ProcessingStatus.choices:
            count = RawOpportunity.objects.filter(status=status).count()
            self.stdout.write(f"  {status}: {count}")
        self.stdout.write(f"  TOTAL: {total_raw}\n")

        # Check recent AI calls
        now = timezone.now()
        recent_calls = AIAPICall.objects.filter(created_at__gte=now - timedelta(hours=1)).order_by('-created_at')

        self.stdout.write(f"AI calls in last hour: {recent_calls.count()}")
        if recent_calls.count() > 0:
            self.stdout.write("Recent calls:")
            for call in recent_calls[:10]:
                self.stdout.write(f"  {call.created_at.strftime('%H:%M:%S')} - {call.provider} {call.operation} {call.context} - {'SUCCESS' if call.success else 'FAILED'}")
        self.stdout.write("")

        # Check AI calls by context
        contexts = AIAPICall.objects.values_list('context', flat=True).distinct()
        self.stdout.write("AI calls by context (last 24h):")
        for context in contexts:
            count = AIAPICall.objects.filter(context=context, created_at__gte=now - timedelta(hours=24)).count()
            self.stdout.write(f"  {context}: {count}")
        self.stdout.write("")

        # Check if there are any running Celery tasks
        from celery import current_app
        try:
            inspect = current_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()

            self.stdout.write("Active Celery tasks:")
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    self.stdout.write(f"  {worker}: {len(tasks)} tasks")
                    for task in tasks[:3]:  # Show first 3
                        self.stdout.write(f"    - {task.get('name', 'unknown')} {task.get('args', '')}")
            else:
                self.stdout.write("  None")

            self.stdout.write(f"\nScheduled tasks: {len(scheduled_tasks) if scheduled_tasks else 0}")

        except Exception as e:
            self.stdout.write(f"Could not check Celery tasks: {e}")

        # Test the new matching behavior
        from profiles.models import UserProfile
        active_opps = Opportunity.objects.filter(status='ACTIVE').count()
        users_with_profiles_count = UserProfile.objects.filter(matching_profile_json__isnull=False).count()
        self.stdout.write("\n--- MATCHING SIMULATION ---")
        self.stdout.write(f"Users with profiles: {users_with_profiles_count}")
        self.stdout.write(f"Active opportunities: {active_opps}")
        if active_opps > 0 and users_with_profiles_count > 0:
            self.stdout.write(f"1 new opportunity would trigger: {users_with_profiles_count} individual user matching tasks")
            self.stdout.write("EXTREME ANTI-BURST: Tasks queued with 10, 20, 30, 40... MINUTE delays")
            self.stdout.write("Rate limited to 15/h total - spreads over 2+ hours to prevent ANY bursts")

        self.stdout.write("\n=== END DEBUG ===")
