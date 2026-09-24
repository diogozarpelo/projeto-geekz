from collections import Counter

from django.db import migrations


def normalize_existing_user_emails(apps, schema_editor):
    user_model = apps.get_model(
        "accounts",
        "User",
    )

    database_alias = schema_editor.connection.alias

    users = list(
        user_model.objects
        .using(database_alias)
        .all()
        .only(
            "pk",
            "email",
        )
        .order_by("pk")
    )

    normalized_by_pk = {
        user.pk: (
            str(user.email or "")
            .strip()
            .lower()
        )
        for user in users
    }

    counts = Counter(
        normalized_by_pk.values()
    )

    duplicate_count = sum(
        1
        for count in counts.values()
        if count > 1
    )

    if duplicate_count:
        raise RuntimeError(
            "Case-insensitive duplicate user emails exist. "
            "Resolve the conflicting accounts before applying "
            "this migration."
        )

    for user in users:
        normalized_email = normalized_by_pk[
            user.pk
        ]

        if normalized_email != user.email:
            (
                user_model.objects
                .using(database_alias)
                .filter(pk=user.pk)
                .update(
                    email=normalized_email,
                )
            )


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.RunPython(
            normalize_existing_user_emails,
            migrations.RunPython.noop,
        ),
    ]
