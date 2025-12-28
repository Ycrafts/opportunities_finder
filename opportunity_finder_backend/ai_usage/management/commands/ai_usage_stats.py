from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Count, Avg, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from ai_usage.models import AIAPICall


class Command(BaseCommand):
    help = "Display AI usage statistics"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        since = timezone.now() - timezone.timedelta(days=days)

        self.stdout.write(f"AI Usage Statistics (last {days} days)")
        self.stdout.write("=" * 50)

        # Total calls
        total_calls = AIAPICall.objects.filter(created_at__gte=since).count()
        successful_calls = AIAPICall.objects.filter(created_at__gte=since, success=True).count()
        failed_calls = AIAPICall.objects.filter(created_at__gte=since, success=False).count()

        self.stdout.write(f"Total API calls: {total_calls}")
        self.stdout.write(f"Successful: {successful_calls} ({successful_calls/total_calls*100:.1f}%)" if total_calls > 0 else "Successful: 0")
        self.stdout.write(f"Failed: {failed_calls} ({failed_calls/total_calls*100:.1f}%)" if total_calls > 0 else "Failed: 0")
        self.stdout.write("")

        # By provider
        provider_stats = AIAPICall.objects.filter(created_at__gte=since).values('provider').annotate(
            total=Count('id'),
            successful=Count('id', filter=models.Q(success=True)),
            avg_duration=Avg('duration_ms'),
            total_tokens=Sum('tokens_used'),
        ).order_by('-total')

        if provider_stats:
            self.stdout.write("By Provider:")
            for stat in provider_stats:
                success_rate = stat['successful'] / stat['total'] * 100 if stat['total'] > 0 else 0
                self.stdout.write(f"  {stat['provider']}: {stat['total']} calls ({success_rate:.1f}% success)")
                if stat['avg_duration']:
                    self.stdout.write(f"    Avg duration: {stat['avg_duration']:.0f}ms")
                if stat['total_tokens']:
                    self.stdout.write(f"    Total tokens: {stat['total_tokens']}")
            self.stdout.write("")

        # By context
        context_stats = AIAPICall.objects.filter(created_at__gte=since).values('context').annotate(
            total=Count('id'),
            successful=Count('id', filter=models.Q(success=True)),
        ).order_by('-total')

        if context_stats:
            self.stdout.write("By Context:")
            for stat in context_stats:
                success_rate = stat['successful'] / stat['total'] * 100 if stat['total'] > 0 else 0
                self.stdout.write(f"  {stat['context']}: {stat['total']} calls ({success_rate:.1f}% success)")
            self.stdout.write("")

        # Recent failures
        recent_failures = AIAPICall.objects.filter(
            created_at__gte=since,
            success=False
        ).order_by('-created_at')[:5]

        if recent_failures:
            self.stdout.write("Recent Failures:")
            for failure in recent_failures:
                self.stdout.write(f"  {failure.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {failure.provider}.{failure.operation}")
                self.stdout.write(f"    Error: {failure.error_message[:100]}...")
            self.stdout.write("")

        # Daily breakdown
        daily_stats = AIAPICall.objects.filter(created_at__gte=since).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            successful=Count('id', filter=models.Q(success=True)),
        ).order_by('date')

        if daily_stats:
            self.stdout.write("Daily Breakdown:")
            for stat in daily_stats:
                success_rate = stat['successful'] / stat['total'] * 100 if stat['total'] > 0 else 0
                self.stdout.write(f"  {stat['date']}: {stat['total']} calls ({success_rate:.1f}% success)")
