from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def save_image(instance, filename):
    ext = filename.split(".")[-1]
    return f"photos/{instance.title}.{ext}"


def image_size_validator(image):
    size_limit = 3
    if image.size > size_limit * 1024 * 1024:
        raise ValidationError(f"Maximum image size is {size_limit}")


class BaseModel(models.Model):
    """
    Base Model class for shared fields.
    """

    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Photo(BaseModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="photos", editable=False
    )
    image = models.ImageField(
        upload_to=save_image, editable=False, validators=[image_size_validator]
    )
    title = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)


# class Review(BaseModel):
#     author = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="reviews", editable=False
#     )
#     photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="reviews")
#     rating = models.IntegerField()
#     body = models.TextField()
