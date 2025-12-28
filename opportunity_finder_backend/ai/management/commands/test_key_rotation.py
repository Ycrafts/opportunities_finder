from django.core.management.base import BaseCommand

from ai.providers.gemini import GeminiAIProvider
from ai.errors import AIError


class Command(BaseCommand):
    help = "Test Gemini API key rotation functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--simulate-quota",
            action="store_true",
            help="Simulate quota exhaustion by using invalid keys",
        )

    def handle(self, *args, **options):
        self.stdout.write("Testing Gemini API Key Rotation")
        self.stdout.write("=" * 50)

        try:
            provider = GeminiAIProvider()
            config = provider.cfg

            self.stdout.write(f"📋 Configured API keys: {len(config.api_keys)}")
            for i, key in enumerate(config.api_keys):
                # Mask the key for security
                masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                self.stdout.write(f"  Key {i+1}: {masked}")

            # Test key selection
            self.stdout.write("\n🎲 Testing key selection...")

            # Reset exhausted keys for testing
            provider._exhausted_keys.clear()

            for i in range(min(3, len(config.api_keys))):
                key = provider._get_next_api_key()
                masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                self.stdout.write(f"  Selection {i+1}: {masked}")

            # Test exhaustion simulation
            if options["simulate_quota"]:
                self.stdout.write("\n⚠️  Simulating quota exhaustion...")

                # Mark all keys as exhausted except one
                for key in config.api_keys[:-1]:
                    provider._mark_key_exhausted(key)

                remaining_key = provider._get_next_api_key()
                masked = remaining_key[:8] + "..." + remaining_key[-4:] if len(remaining_key) > 12 else "***"
                self.stdout.write(f"  Remaining key: {masked}")

                # Try to get another key (should cycle back if multiple available)
                if len(config.api_keys) > 1:
                    try:
                        next_key = provider._get_next_api_key()
                        masked_next = next_key[:8] + "..." + next_key[-4:] if len(next_key) > 12 else "***"
                        self.stdout.write(f"  Next key (round-robin): {masked_next}")
                    except Exception as e:
                        self.stdout.write(f"  Round-robin result: {e}")

            self.stdout.write("\n✅ Key rotation test completed successfully!")

        except AIError as e:
            self.stderr.write(self.style.ERROR(f"❌ Test failed: {e}"))
            if "API key" in str(e).lower():
                self.stderr.write("💡 Make sure GEMINI_API_KEYS is set in your .env file")
                self.stderr.write("   Example: GEMINI_API_KEYS=key1,key2,key3")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Unexpected error: {e}"))
