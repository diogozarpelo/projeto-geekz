from django.db import migrations


def create_initial_colors_and_sizes(apps, schema_editor):
    Color = apps.get_model("catalog", "Color")
    Size = apps.get_model("catalog", "Size")

    colors = [
        {
            "name": "Preto",
            "slug": "preto",
            "hex_code": "#000000",
            "sort_order": 1,
        },
        {
            "name": "Branco",
            "slug": "branco",
            "hex_code": "#FFFFFF",
            "sort_order": 2,
        },
        {
            "name": "Cinza",
            "slug": "cinza",
            "hex_code": "#808080",
            "sort_order": 3,
        },
    ]

    sizes = [
        {"name": "P", "slug": "p", "sort_order": 1},
        {"name": "M", "slug": "m", "sort_order": 2},
        {"name": "G", "slug": "g", "sort_order": 3},
        {"name": "GG", "slug": "gg", "sort_order": 4},
        {"name": "XG", "slug": "xg", "sort_order": 5},
    ]

    for color in colors:
        Color.objects.get_or_create(
            slug=color["slug"],
            defaults={
                "name": color["name"],
                "hex_code": color["hex_code"],
                "sort_order": color["sort_order"],
                "is_active": True,
            },
        )

    for size in sizes:
        Size.objects.get_or_create(
            slug=size["slug"],
            defaults={
                "name": size["name"],
                "sort_order": size["sort_order"],
                "is_active": True,
            },
        )


def remove_initial_colors_and_sizes(apps, schema_editor):
    Color = apps.get_model("catalog", "Color")
    Size = apps.get_model("catalog", "Size")

    Color.objects.filter(
        slug__in=[
            "preto",
            "branco",
            "cinza",
        ]
    ).delete()

    Size.objects.filter(
        slug__in=[
            "p",
            "m",
            "g",
            "gg",
            "xg",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_seed_initial_categories"),
    ]

    operations = [
        migrations.RunPython(
            create_initial_colors_and_sizes,
            remove_initial_colors_and_sizes,
        ),
    ]