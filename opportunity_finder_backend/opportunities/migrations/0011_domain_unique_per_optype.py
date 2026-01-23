from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0010_source_consecutive_failures_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name="domain",
            unique_together={("opportunity_type", "name")},
        ),
        migrations.AddIndex(
            model_name="domain",
            index=models.Index(fields=["opportunity_type", "name"], name="opportunit_oppo_type_name_idx"),
        ),
    ]
