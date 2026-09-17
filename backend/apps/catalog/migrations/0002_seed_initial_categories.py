from django.db import migrations


def create_initial_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")

    categories = [
        {
            "name": "Games",
            "slug": "games",
            "sort_order": 1,
        },
        {
            "name": "Animes",
            "slug": "animes",
            "sort_order": 2,
        },
        {
            "name": "Filmes/S\u00e9ries",
            "slug": "filmes-series",
            "sort_order": 3,
        },
    ]

    for category in categories:
        Category.objects.get_or_create(
            slug=category["slug"],
            defaults={
                "name": category["name"],
                "sort_order": category["sort_order"],
                "is_active": True,
            },
        )


def remove_initial_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")

    Category.objects.filter(
        slug__in=[
            "games",
            "animes",
            "filmes-series",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_initial_categories,
            remove_initial_categories,
        ),
    ]
