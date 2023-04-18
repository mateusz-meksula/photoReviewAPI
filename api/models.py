from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)

User = get_user_model()


def save_image(instance, filename):
    """
    Save image file to the '/media/photos/' with `title` as file name.
    """

    ext = filename.split(".")[-1]
    return f"photos/{instance.title}.{ext}"


def image_size_validator(image):
    """
    Raise `ValidationError` when image size is greater than `size_limit`.
    """

    # image size limit in MB
    size_limit = 3
    if image.size > size_limit * 1024 * 1024:
        raise ValidationError(f"Maximum image size is {size_limit}")


def tag_name_validator(name: str):
    if not name.isalpha():
        raise ValidationError("Tag name must be an alphabetic string.")


class BaseModel(models.Model):
    """
    Base Model class for shared fields.
    """

    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.CharField(
        max_length=20, unique=True, db_index=True, validators=[tag_name_validator]
    )

    def __str__(self) -> str:
        return self.name


class Photo(BaseModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="photos", editable=False
    )
    image = models.ImageField(upload_to=save_image, validators=[image_size_validator])
    title = models.CharField(max_length=50, unique=True)
    tags = models.ManyToManyField(Tag, related_name="photos")
    description = models.TextField(null=True, blank=True)


class Review(BaseModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews", editable=False
    )
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )
    body = models.TextField(null=True, blank=True)
