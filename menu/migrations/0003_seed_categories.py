from django.db import migrations


def seed_categories(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    categories = ["Fast Food", "Drinks", "Desserts", "Burger", "Pizza", "BBQ", "Sandwich", "Chinese"]
    for name in categories:
        Category.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0002_food_created_at_food_updated_at_alter_food_category_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_categories),
    ]
