import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Photo


@receiver(post_delete, sender=Photo)
def image_delete_from_media(sender, instance, **kwargs):
    """
    Deletes image file from /media directory when Photo instance is deleted.
    """
    instance.image.delete(save=False)


@receiver(pre_save, sender=Photo)
def image_rename_after_patch(sender, instance, **kwargs):
    """
    Renames image file when user updates photo title.
    """

    # perform action only on existing instances
    if instance.pk:
        old_name = sender.objects.get(pk=instance.id).image.url
        ext = old_name.split(".")[-1]
        title = instance.title.replace(" ", "_")
        new_name = f"media/photos/{title}.{ext}"

        # perform action only when title changed
        if os.path.isfile(old_name[1:]) and new_name != old_name[-1]:
            os.rename(old_name[1:], new_name)
            instance.image = new_name.replace("media/", "", 1)
