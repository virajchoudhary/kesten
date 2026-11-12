import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def create_security_state_for_existing_users(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    user_model = apps.get_model(app_label, model_name)
    state_model = apps.get_model("accounts", "AccountSecurityState")
    database = schema_editor.connection.alias
    batch = []
    user_ids = (
        user_model._default_manager.using(database)
        .order_by()
        .values_list("pk", flat=True)
        .iterator(chunk_size=500)
    )
    for user_id in user_ids:
        batch.append(state_model(user_id=user_id))
        if len(batch) == 500:
            state_model.objects.using(database).bulk_create(batch, batch_size=500)
            batch.clear()
    if batch:
        state_model.objects.using(database).bulk_create(batch, batch_size=500)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountSecurityState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("session_epoch", models.PositiveBigIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_security_state",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AccountInvitation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("reserved_username", models.CharField(max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                (
                    "token_digest",
                    models.CharField(editable=False, max_length=64, unique=True),
                ),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "issued_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="account_invitations_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["reserved_username", "consumed_at", "revoked_at"],
                        name="acct_invite_status",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token_digest", models.CharField(max_length=64, unique=True, editable=False)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "issued_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="account_password_resets_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_password_reset_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["user", "expires_at"], name="acct_reset_user_expiry"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="LoginAttemptState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identifier_digest",
                    models.CharField(editable=False, max_length=64, unique=True),
                ),
                ("failure_count", models.PositiveSmallIntegerField(default=0)),
                (
                    "window_started_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(
            create_security_state_for_existing_users,
            migrations.RunPython.noop,
        ),
    ]
