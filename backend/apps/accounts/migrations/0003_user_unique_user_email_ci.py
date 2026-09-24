import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0002_normalize_existing_user_emails",
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower(
                    "email"
                ),
                name="unique_user_email_ci",
            ),
        ),
    ]
