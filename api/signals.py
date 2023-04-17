import os

from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver

from .models import Photo


@receiver(post_delete, sender=Photo)
def image_delete_from_media(sender, instance, **kwargs):
    instance.image.delete(save=False)


@receiver(post_save, sender=Photo)
def image_rename_after_patch(sender, instance, created, **kwargs):
    if not created:
        old_name = sender.objects.get(pk=instance.id).image.url
        ext = old_name.split(".")[-1]
        t = instance.title.replace(" ", "_")
        new_name = f"media/photos/{t}.{ext}"

        if os.path.isfile(old_name[1:]):
            os.rename(old_name[1:], new_name)
