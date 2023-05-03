# <img src="./photo_reviewapi_header.jpg">

## About the Project

Photo Review API is a web API that allows users to upload and rate images.  
The API has the following functionalities:
<ul>
    <li>user registration along with password reset functionality</li>
    <li>JWT authentication</li>
    <li>image upload</li>
    <li>tags system for images</li>
    <li>rating system for images</li>
</ul>

Account management for the API is provided by [flash-accounts](https://github.com/mateusz-meksula/flash-accounts) package, and JWT authentication is provided by [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) plugin.

Photo Review API was built with Django and Django REST Framework, with data managed by a PostgreSQL database.

## Overview

Photo Review API has the following endpoints:

```python
- /api/auth/sign-up/
- /api/auth/password-reset/
- /api/auth/password-reset/confirm/<str:token>/
- /api/auth/token/
- /api/auth/token/refresh/

- /api/photos/
- /api/photos/<int:photo_id>/
- /api/photos/<int:photo_id>/reviews/
- /api/photos/<int:photo_id>/reviews/<int:review_id>/

- /api/tags/
- /api/tags/<str:tag_name>/
```

## Challenges & Solutions

### Tagging system

The challenge was to implement tagging system for images, so that users could associate their images with topics or keywords.  

In order to achieve that, a `Tag` model was created...

```python
class Tag(models.Model):
    name = models.CharField(
        max_length=20, unique=True, db_index=True, validators=[tag_name_validator]
    )

    def __str__(self) -> str:
        return self.name

def tag_name_validator(name: str):
    if not name.isalpha():
        raise ValidationError("Tag name must contain only alphabetic characters.")
```

...and `ManyToMany` relationship field was added to the `Photo` model:

```python
class Photo(BaseModel):
    # ...
    tags = models.ManyToManyField(Tag, related_name="photos")
    # ...
```

Thit allows images to be associated with multiple tags and vice versa.  
The design choice was made to enable users to add tags and images in a single POST request and specify tags by their `name` field instead of their `id` field. To meet these requirements, a `PhotoCreateSerializer` was written as follows:

```python
class PhotoCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    tags = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Photo
        fields = ["id", "image", "title", "description", "tags"]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        photo = Photo.objects.create(**validated_data)

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            photo.tags.add(tag)

        return photo
```

With that, users can provide tags as a list of strings and when `create` method is called, it loops through the list, retrieves a `Tag` instance with the given name or creates a new `Tag` instance if one with the given name is not in the database. Finally, it adds tags to the `tags` field of an newly created `Photo` instance.  
A similar approach was implemented for the `PhotoPatchSerializer` using the `update` method:

```python
class PhotoPatchSerializer(serializers.ModelSerializer):
    # ...

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags_data = validated_data.pop("tags", [])

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            instance.tags.add(tag)

        return super().update(instance, validated_data)
```

When the `update` method is called, the first thing it does is removing all previously assigned tags to ensure that only tags provided by the user in the PATCH request are assigned to the photo. 

### Review system

## Frontend JavaScript client

## Running project locally