import os

from django.db.models.signals import post_delete, post_save, pre_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver

from megaone.users.models import RestaurantTable
from .models import LoyaltyCard

User = get_user_model()


@receiver(post_save, sender=User)
def create_loyalty_card_for_user(sender, instance, created, **kwargs):
    if instance.is_staff or instance.is_superuser or getattr(instance, 'is_kitchen', False):
        return

    card, was_created = LoyaltyCard.objects.get_or_create(
        user=instance,
        defaults={'status': 'ACTIVE'}
    )

    if was_created or not card.card_pdf or not card.qr_code_image:
        from .loyalty_utils import generate_qr_code_image, generate_loyalty_card_pdf, generate_loyalty_card_image
        try:
            generate_qr_code_image(card)
            generate_loyalty_card_pdf(card)
            generate_loyalty_card_image(card)
        except Exception:
            pass


@receiver(post_delete, sender=RestaurantTable)
def delete_qr_on_table_delete(sender, instance, **kwargs):
    if instance.qr_code_image and os.path.isfile(instance.qr_code_image.path):
        os.remove(instance.qr_code_image.path)


@receiver(pre_save, sender=RestaurantTable)
def delete_old_qr_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = RestaurantTable.objects.get(pk=instance.pk)
    except RestaurantTable.DoesNotExist:
        return
    if old.qr_code_image and old.qr_code_image != instance.qr_code_image and os.path.isfile(old.qr_code_image.path):
        os.remove(old.qr_code_image.path)
