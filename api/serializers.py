from rest_framework import serializers

from .models import Photo, Tag


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

    class Meta:
        model = Photo
        fields = "__all__"


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
