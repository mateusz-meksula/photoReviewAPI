from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Photo, Tag, Review


class ReviewRelatedHyperLink(serializers.HyperlinkedRelatedField):
    """
    Custom `HyperlinkedRelatedField` class for `Review` instances
    that require `photo_id` in their url.
    """

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


class ReviewIdHyperLink(serializers.HyperlinkedIdentityField):
    """
    Custom `HyperlinkedIdentityField` class for `Review` instances
    that require `photo_id` in their url.
    """

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


class PhotoCreateSerializer(serializers.ModelSerializer):
    """
    Photo serializer for create action.
    """

    image = serializers.ImageField(required=True)
    tags = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Photo
        fields = ["id", "image", "title", "description", "tags"]

    def create(self, validated_data):
        """
        Creates photo object and assigns provided tags to it.
        """

        tags_data = validated_data.pop("tags", [])
        photo = Photo.objects.create(**validated_data)

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            photo.tags.add(tag)

        return photo


class PhotoDetailSerializer(serializers.ModelSerializer):
    """
    Photo serializer for retrieve action.
    """

    author = serializers.CharField(source="author.username")
    tags = serializers.StringRelatedField(many=True)
    average_rating = serializers.FloatField()
    reviews = ReviewRelatedHyperLink(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")

    class Meta:
        model = Photo
        fields = [
            "id",
            "author",
            "title",
            "image",
            "description",
            "average_rating",
            "created_at",
            "updated_at",
            "tags",
            "reviews",
        ]


class PhotoListSerializer(serializers.HyperlinkedModelSerializer):
    """
    Photo serializer for list action.
    """

    author = serializers.CharField(source="author.username")
    average_rating = serializers.FloatField()

    class Meta:
        model = Photo
        fields = [
            "id",
            "url",
            "author",
            "title",
            "image",
            "average_rating",
        ]


class PhotoPatchSerializer(serializers.ModelSerializer):
    """
    Photo serializer for partial update action.
    Only `title` and `description` could by modified.
    """

    tags = serializers.ListField(write_only=True, required=False)
    title = serializers.CharField(required=False)

    class Meta:
        model = Photo
        fields = ["title", "description", "tags"]

    def update(self, instance, validated_data):
        """
        Removes all previous tags and adds provided tags.
        """

        instance.tags.clear()
        tags_data = validated_data.pop("tags", [])

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            instance.tags.add(tag)

        return super().update(instance, validated_data)


class TagSerializer(serializers.ModelSerializer):
    """
    Tag serializer for list action.
    """

    photos = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="photo-detail"
    )
    number_of_photos = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = ["id", "name", "number_of_photos", "photos"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Review serializer for create action.
    """

    class Meta:
        model = Review
        fields = ["id", "rating", "body"]


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Review serializer for list action.
    """

    author = serializers.CharField(source="author.username")
    url = ReviewIdHyperLink(view_name="review-detail")

    class Meta:
        model = Review
        fields = ["id", "url", "author", "rating", "body"]


class ReviewDetailSerializer(serializers.ModelSerializer):
    """
    Review serializer for retrieve action.
    """

    author = serializers.CharField(source="author.username")
    photo = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="photo-detail"
    )
    created_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")

    class Meta:
        model = Review
        fields = [
            "id",
            "author",
            "rating",
            "body",
            "created_at",
            "updated_at",
            "photo",
        ]


class ReviewPatchSerializer(serializers.ModelSerializer):
    """
    Review serializer for partial updated action.
    """

    rating = serializers.IntegerField(required=False)

    class Meta:
        model = Review
        fields = ["rating", "body"]
