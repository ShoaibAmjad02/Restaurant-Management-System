from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User, RestaurantTable, Invoice, KitchenOrder, LoyaltyCard, LoyaltyTransaction, QRTableOffer

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "name", "is_superuser"]
    search_fields = ["name"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ["table_no", "qr_token", "created_at"]
    search_fields = ["table_no"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "table_no", "total_amount", "created_at"]
    search_fields = ["invoice_number", "table_no"]


@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "table_no", "status", "created_at"]
    search_fields = ["order_number", "table_no"]


@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = ["card_number", "user", "total_points", "used_points", "remaining_points", "status", "created_at"]
    search_fields = ["card_number", "user__name", "user__email"]
    list_filter = ["status"]


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ["card", "transaction_type", "earned_points", "redeemed_points", "remaining_balance", "order_number", "created_at"]
    search_fields = ["card__card_number", "order_number"]
    list_filter = ["transaction_type"]


@admin.register(QRTableOffer)
class QRTableOfferAdmin(admin.ModelAdmin):
    list_display = ["discount_percentage", "is_active", "start_datetime", "end_datetime", "created_at"]
    list_filter = ["is_active"]
