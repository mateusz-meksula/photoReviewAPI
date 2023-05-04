# <img src="./photo_reviewapi_header.jpg">

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

The challenge was to implement tagging system for photos, so that users could associate their photos with topics or keywords.

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

That allows `Photo` instances to be associated with multiple tags and vice versa.  
The design choice was made to enable users to add tags and photos in a single POST request and specify tags by their `name` field instead of their `id` field. To meet these requirements, a `PhotoCreateSerializer` was written as follows:

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

The challenge was to implement a review system for photos, so that users could rate photos on a scale from 1 to 5 and optionally write what they think about the photo.

The first step was to create a `Review` model with `ForeignKey` field referencing the `Photo` model:

```python
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
```

The design choice was made to nest the reviews endpoints into the photo retrieve endpoint:

```
/api/photos/<int:photo_id>/reviews/
```

This approach allows the API to retrieve only the reviews added to a specific photo, resulting in a more targeted response.

Nested reviews URLs were achieved by creating separate router for reviews and including its URLs on top of the photo retrieve endpoint:

```python
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
class ReviewViewSet(ModelViewSet):
    # ...

    def get_queryset(self):
        photo = get_object_or_404(Photo, pk=self.kwargs["photo_id"])
        return photo.reviews.all()
```

The photo retrieve endpoint `/api/photos/<int:photo_id>/` returns photo data together with a list of the photo's review URLs. However, since the review retrieve endpoint `/api/photos/<int:photo_id>/reviews/<int:review_id>/` requires two path variables, the `HyperlinkedRelatedField` could not be used directly.  
The solution to that problem was to create a custom hyperlinked related field...

```python
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
class PhotoViewSet(ModelViewSet):
    # ...
    queryset = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
    # ...
```

## Frontend JavaScript client

For presentational purposes, this project includes a minimalistic frontend Django app that enables users to interact with the web API using a JavaScript API client.  

![photoreviewAPI2](https://user-images.githubusercontent.com/108681279/236194936-dc3c704e-2bdd-4810-a03d-85909ab47d7d.gif)

The page presented above is located at the project's root URL.  
The API client also enables sending data to the server:


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
