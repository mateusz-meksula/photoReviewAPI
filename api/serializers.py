from rest_framework import serializers

from .models import Photo


class PhotoCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = Photo
        fields = ["id", "image", "title", "description"]


class PhotoDetailSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")

    class Meta:
        model = Photo
        fields = "__all__"


class PhotoPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["title", "description"]
