from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.utils import timezone
from .models import LoyaltyCard, LoyaltyTransaction
from menu.models import Food

User = get_user_model()


@receiver(post_save, sender=User)
def create_loyalty_card_on_registration(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        if not LoyaltyCard.objects.filter(user=instance).exists():
            card = LoyaltyCard.objects.create(
                user=instance,
                status='ACTIVE',
            )
            from .utils import generate_loyalty_card_pdf, generate_loyalty_card_image
            try:
                generate_loyalty_card_pdf(card)
                generate_loyalty_card_image(card)
            except Exception:
                pass


@receiver(post_save, sender=User)
def create_loyalty_card_for_existing_users(sender, instance, **kwargs):
    if not instance.is_staff and not instance.is_superuser:
        LoyaltyCard.objects.get_or_create(
            user=instance,
            defaults={'status': 'ACTIVE'}
        )
