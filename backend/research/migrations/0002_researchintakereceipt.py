import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("research", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResearchIntakeReceipt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("version", models.CharField(max_length=64)),
                ("evidence", models.JSONField()),
                ("csv_content", models.BinaryField(max_length=2_000_000)),
                ("terms_content", models.BinaryField(max_length=1_000_000)),
                ("availability_content", models.BinaryField(max_length=2_000_000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approved_research_intakes", to=settings.AUTH_USER_MODEL)),
                ("dataset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="intake_receipts", to="research.researchdataset")),
            ],
            options={
                "ordering": ["created_at", "id"],
                "constraints": [models.UniqueConstraint(fields=("dataset", "version"), name="research_intake_dataset_version")],
            },
        ),
    ]
