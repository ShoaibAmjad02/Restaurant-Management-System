from django.contrib import admin
from .models import Food


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "available",
        "is_popular",
    )

    list_filter = (
        "is_popular",
        "available",
    )

    search_fields = (
        "name",
    )