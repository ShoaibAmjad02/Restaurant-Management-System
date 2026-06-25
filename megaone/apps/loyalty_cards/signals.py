from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import LoyaltyCard

User = get_user_model()


@receiver(post_save, sender=User)
def create_loyalty_card_for_user(sender, instance, created, **kwargs):
    """Create a loyalty card ONLY for online registered customers.

    Excluded:
        - Staff / Superusers / Kitchen users
        - QR table customers (no User account)
        - Guest / walk-in customers (no User account)
    """
    if instance.is_staff or instance.is_superuser or getattr(instance, 'is_kitchen', False):
        return

    card, was_created = LoyaltyCard.objects.get_or_create(
        user=instance,
        defaults={'status': 'ACTIVE'}
    )

    if was_created or not card.card_pdf or not card.qr_code_image:
        from .utils import generate_qr_code_image, generate_loyalty_card_pdf, generate_loyalty_card_image
        try:
            generate_qr_code_image(card)
            generate_loyalty_card_pdf(card)
            generate_loyalty_card_image(card)
        except Exception:
            pass
