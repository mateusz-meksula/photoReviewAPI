from rest_framework import serializers
from django.db.models import Avg
from rest_framework.reverse import reverse

from .models import Photo, Tag, Review


class ReviewHyperLink(serializers.HyperlinkedRelatedField):
    view_name = "review-detail"

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            "photo_id": obj.photo.id,
            "pk": obj.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


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
        """ """
        tags_data = validated_data.pop("tags", [])
        photo = Photo.objects.create(**validated_data)

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            photo.tags.add(tag)

        return photo


class PhotoDetailSerializer(serializers.ModelSerializer):
    """
    Photo serializer for retrieve and list actions.
    """

    author = serializers.CharField(source="author.username")
    tags = serializers.StringRelatedField(many=True)
    average_rating = serializers.SerializerMethodField()
    # reviews = serializers.HyperlinkedRelatedField(
    #     many=True, read_only=True, view_name="review-detail"
    # )
    reviews = ReviewHyperLink(many=True, read_only=True)

    class Meta:
        model = Photo
        fields = "__all__"

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            avg = reviews.aggregate(Avg("rating"))
            return round(avg["rating__avg"], 2)
        else:
            return None


class PhotoListSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.CharField(source="author.username")
    average_rating = serializers.SerializerMethodField()

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

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            avg = reviews.aggregate(Avg("rating"))
            return round(avg["rating__avg"], 2)
        else:
            return None


class PhotoPatchSerializer(serializers.ModelSerializer):
    """
    Photo serializer for patch method.
    Only `title` and `description` could by modified.
    """

    tags = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Photo
        fields = ["title", "description", "tags"]

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags_data = validated_data.pop("tags", [])

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            instance.tags.add(tag)

        return super().update(instance, validated_data)


class TagListSerializer(serializers.ModelSerializer):
    photos = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="photo-detail"
    )

    class Meta:
        model = Tag
        fields = ["id", "name", "photos"]


class TagDetailSerializer(serializers.ModelSerializer):
    photos = PhotoDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "photos"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "rating", "body"]


class ReviewListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")

    class Meta:
        model = Review
        fields = ["id", "author", "rating", "body"]


class ReviewDetailSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")
    photo = PhotoDetailSerializer(read_only=True)

    class Meta:
        model = Review
        fields = "__all__"


class ReviewPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "body"]
