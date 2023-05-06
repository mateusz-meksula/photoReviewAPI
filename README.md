# <img src="./photo_review_api_header.jpg">

## About the Project

Photo Review API is a web API that allows users to upload and rate photos.  
The API has the following functionalities:

<ul>
    <li>user registration along with password reset functionality</li>
    <li>JWT authentication</li>
    <li>image upload</li>
    <li>tags system for photos</li>
    <li>rating system for photos</li>
</ul>

Account management for the API is provided by [flash-accounts](https://github.com/mateusz-meksula/flash-accounts) package, and JWT authentication is provided by [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) plugin.

Photo Review API was built with Django and Django REST Framework, with data managed by a PostgreSQL database.

## Using the API

### Signing-up

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user1",
        "email": "user01@user.com",
        "password": "user1password123",
        "password2": "user1password123"
    }' \
    http://localhost:8000/api/auth/sign-up/
```

For a quicker start, the account activation feature of [flash-accounts](https://github.com/mateusz-meksula/flash-accounts) has been disabled. However, to change password, users must provide a valid and existing email.

### Authentication

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user1",
        "password": "user1password123"
    }' \
    http://localhost:8000/api/auth/token/
```

The above request returns both the `access` token and the `refresh` token. To authenticate, an `Authorization` header must be added to request headers:

```bash
curl -X POST \
...
    -H "Authorization: Bearer {access_token_value}" \ 
...
```

### Adding a photo

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -H "Authorization: Bearer {access_token_value}" \
    -F "image=@./my_image.png" \
    -F "title=little turtles" \
    -F "tags[1]=nature" \
    -F "tags[2]=animals" \
    http://localhost/api/photos/
```

### Updating a photo

```bash
curl -X PATCH \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer {access_token_value}" \
    -d '{"title": "new title"} \
    http://localhost:8000/api/photos/<int:photo_id>/
```

### Deleting a photo

```bash
curl -X DELETE \
    -H "Authorization: Bearer {access_token_value}" \
    http://localhost:8000/api/photos/<int:photo_id>/
```

### Reviewing a photo

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer {access_token_value}" \
    -d '{
        "rating": 4,
        "body": "good photo"
    }' \
    http://localhost/api/photos/<int:photo_id>/reviews/
```

It is important to mention that a user cannot review his own photos.

### Updating a review

```bash
curl -X PATCH \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer {access_token_value}" \
    -d '{"rating": 5} \
    http://localhost:8000/api/photos/<int:photo_id>/reviews/<int:review_id>/
```

### Deleting a review

```bash
curl -x DELETE \
    -H "Authorization: Bearer {access_token_value}" \
    http://localhost:8000/api/photos/<int:photo_id>/reviews/<int:review_id>/
```

### Photo list and detail endpoints

List of all photos:
```bash
curl http://localhost:8000/api/photos/
```

The number of results can be limited using the `limit` query parameter, and the results can be filtered by field names. The `ordering` query parameter can be used to order the results:

```bash
curl http://localhost:8000/api/photos/?limit=3
curl http://localhost:8000/api/photos/?title=little%20turtles
curl http://localhost:8000/api/photos/?ordering=created_at
```

The results can be also filtered using `search` query parameter: 

```bash
curl http://localhost:8000/api/photos/?search=nature
```

A request to the photo detail endpoint is made by providing a photo id:

```bash
curl http://localhost:8000/api/photos/<int:photo_id>/
```

### Review list and detail endpoints

List of reviews for a given photo:
```bash
curl http://localhost:8000/api/photos/<int:photo_id>/reviews/
```

A request to the review detail endpoint is made by providing a review id:

```bash
curl http://localhost:8000/api/photos/<int:photo_id>/reviews/<int:review_id>/
```

### Tag list and detail endpoints

```bash
curl http://localhost:8000/api/tags/
```

The number of results can be limited using the `limit` query parameter, and the results can be filtered by field names. The `ordering` query parameter can be used to order the results:

```bash
curl http://localhost:8000/api/tags/?limit=3
curl http://localhost:8000/api/tags/?id=2
curl http://localhost:8000/api/tags/?ordering=-number_of_photos
```

The results can be also filtered using `search` query parameter: 

```bash
curl http://localhost:8000/api/tags/?search=nature
```

A request to the tag detail endpoint is made by providing a tag name:

```bash
curl http://localhost:8000/api/tag/nature/
```

## Challenges & Solutions

### Tagging system

The challenge was to implement tagging system for photos, so that users could associate their photos with topics or keywords.

In order to achieve that, a `Tag` model was created...

```python
from django.db import models
from django.core.exceptions import ValidationError

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
from django.db import models

class Photo(models.Model):
    # ...
    tags = models.ManyToManyField(Tag, related_name="photos")
    # ...
```

That allows `Photo` instances to be associated with multiple tags and vice versa.  
The design choice was made to enable users to add tags and photos in a single POST request and specify tags by their `name` field instead of their `id` field. To meet these requirements, a `PhotoCreateSerializer` was written as follows:

```python
from rest_framework import serializers

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
from rest_framework import serializers

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

The challenge was to implement a review system for photos, so that users could rate photos on a scale from 1 to 5 and optionally write what they think about the photo.

The first step was to create a `Review` model with `ForeignKey` field referencing the `Photo` model:

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
User = get_user_model()

class Review(models.Model):
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
```

The design choice was made to nest the reviews endpoints into the photo retrieve endpoint:

```
/api/photos/<int:photo_id>/reviews/
```

This approach allows the API to retrieve only the reviews added to a specific photo, resulting in a more targeted response.

Nested reviews URLs were achieved by creating separate router for reviews and including its URLs on top of the photo retrieve endpoint:

```python
from djago.urls import path, include
from rest_framework.routers import SimpleRouter

# ...
router = SimpleRouter()
router.register(r"photos", views.PhotoViewSet, basename="photo")
urlpatterns += router.urls

reviews_router = SimpleRouter()
reviews_router.register("reviews", views.ReviewViewSet, basename="review")
urlpatterns += [path("photos/<int:photo_id>/", include(reviews_router.urls))]
```

To ensure that only reviews related to the `photo_id` are returned, the `get_queryset` method of the `ReviewViewSet` was overwritten:

```python
from rest_framework.viewsets import ModelViewSet

class ReviewViewSet(ModelViewSet):
    # ...

    def get_queryset(self):
        photo = get_object_or_404(Photo, pk=self.kwargs["photo_id"])
        return photo.reviews.all()
```

The photo retrieve endpoint `/api/photos/<int:photo_id>/` returns photo data together with a list of the photo's review URLs. However, since the review retrieve endpoint `/api/photos/<int:photo_id>/reviews/<int:review_id>/` requires two path variables, the `HyperlinkedRelatedField` could not be used directly.  
The solution to that problem was to create a custom hyperlinked related field...

```python
from rest_framework import serializers
from rest_framework.reverse import reverse

class ReviewRelatedHyperLink(serializers.HyperlinkedRelatedField):
    view_name = "review-detail"

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            "photo_id": obj.photo.id,
            "pk": obj.id,
        }
        return reverse(
            view_name,
            kwargs=url_kwargs,
            request=request,
            format=format,
        )
```

...and declare it in the `PhotoDetailSerializer`:

```python
from rest_framework import serializers

class PhotoDetailSerializer(serializers.ModelSerializer):
    # ...
    reviews = ReviewRelatedHyperLink(many=True, read_only=True)
    # ...

    class Meta:
        model = Photo
        fields = [
            # ...
            "reviews",
            # ...
        ]
```

The response data for photos includes an `average_rating` field, which was obtained by annotating the query set:

```python
from rest_framework.viewsets import ModelViewSet
from .models import Photo

class PhotoViewSet(ModelViewSet):
    # ...
    queryset = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
    # ...
```

## Frontend JavaScript client

For presentational purposes, this project includes a minimalistic frontend Django app that enables users to interact with the web API using a JavaScript API client.  

![pra](https://user-images.githubusercontent.com/108681279/236201934-d166161d-72c9-4c26-873c-a85b64b94b10.gif)

The page presented above is located at the project's root URL.  
The API client also enables sending data to the server:

![pratoken](https://user-images.githubusercontent.com/108681279/236200685-02cca9cc-7d5f-4c88-ac10-34169771639b.gif)

In the above example, a keyboard shortcut `Ctrl` + `p` was used to pretty format entered JSON.


## Running project locally

The project in this repository is fully functional, but it has not been prepared for deployment. However, the project is containerized, allowing for easy setup on any machine with Docker installed.

To run project in local environment, follow these steps:

1. Clone repository by running the following command:
```bash
git clone https://github.com/mateusz-meksula/photoReviewAPI.git
```

2. Run project using docker compose:
```bash
docker compose up --build
```

The project will be available at [http://localhost:8000](http://localhost:800).
