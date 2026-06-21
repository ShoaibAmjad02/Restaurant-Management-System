import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from megaone.users.models import RestaurantTable


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
