from django.contrib import admin
from .models import LoyaltyCard, LoyaltyTransaction


class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'customer_name', 'customer_email', 'total_points', 'used_points', 'remaining_points', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('card_number', 'user__name', 'user__email')
    readonly_fields = ('card_number', 'total_points', 'used_points', 'remaining_points', 'qr_token', 'created_at', 'updated_at')
    inlines = [LoyaltyTransactionInline]

    def customer_name(self, obj):
        return obj.user.name if obj.user else 'N/A'
    customer_name.short_description = 'Customer'

    def customer_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    customer_email.short_description = 'Email'


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('card', 'transaction_type', 'earned_points', 'redeemed_points', 'remaining_balance', 'order_number', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('card__card_number', 'order_number')
