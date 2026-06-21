import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from menu.models import Food


@receiver(post_delete, sender=Food)
def delete_food_image_on_delete(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)


@receiver(pre_save, sender=Food)
def delete_old_food_image_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Food.objects.get(pk=instance.pk)
    except Food.DoesNotExist:
        return
    if old.image and old.image != instance.image and os.path.isfile(old.image.path):
        os.remove(old.image.path)
