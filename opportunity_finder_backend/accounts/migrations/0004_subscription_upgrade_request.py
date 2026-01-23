from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_subscription_level"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionUpgradeRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("payment_method", models.CharField(default="Telebirr", max_length=50)),
                ("receipt", models.FileField(blank=True, upload_to="subscription_receipts/")),
                ("note", models.TextField(blank=True, default="")),
                ("admin_note", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_subscription_requests", to="accounts.user")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscription_requests", to="accounts.user")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
