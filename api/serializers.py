from rest_framework import serializers

from .models import Photo


class PhotoCreateSerializer(serializers.ModelSerializer):
    """
    Photo serializer for create action.
    """

    image = serializers.ImageField(required=True)

    class Meta:
        model = Photo
        fields = ["id", "image", "title", "description"]


class PhotoDetailSerializer(serializers.ModelSerializer):
    """
    Photo serializer for retrieve and list actions.
    """

    author = serializers.CharField(source="author.username")

    class Meta:
        model = Photo
        fields = "__all__"


class PhotoPatchSerializer(serializers.ModelSerializer):
    """
    Photo serializer for patch method.
    Only `title` and `description` could by modified.
    """

    class Meta:
        model = Photo
        fields = ["title", "description"]
