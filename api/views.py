from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import generics
from rest_framework import permissions

from .models import Photo, Tag, Review
from . import serializers


class PhotoViewSet(ModelViewSet):
    """
    ViewSet for Photo instances management.
    """

    queryset = Photo.objects.all()

    # exclude `put` HTTP method
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]

    def get_permissions(self):
        """
        Set permission depending on the action.
        """

        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.AllowAny]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsAuthor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Set serializer class depending on the action.
        """

        if self.action == "create":
            return serializers.PhotoCreateSerializer
        if self.action in ("list", "retrieve", "destroy"):
            return serializers.PhotoDetailSerializer
        if self.action == "partial_update":
            return serializers.PhotoPatchSerializer

    def perform_create(self, serializer):
        """
        Assigns authenticated user to the photo instance.
        """
        serializer.save(author=self.request.user)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    lookup_field = "name"

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.TagListSerializer
        if self.action == "retrieve":
            return serializers.TagDetailSerializer


class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    # exclude `put` HTTP method
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]

    def get_queryset(self):
        photo = Photo.objects.get(id=self.kwargs["photo_id"])
        return photo.reviews.all()

    def get_permissions(self):
        """
        Set permission depending on the action.
        """

        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.AllowAny]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsAuthor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Set serializer class depending on the action.
        """

        if self.action == "create":
            return serializers.ReviewCreateSerializer
        if self.action == "list":
            return serializers.ReviewListSerializer
        if self.action in ("retrieve", "destroy"):
            return serializers.ReviewDetailSerializer
        if self.action == "partial_update":
            return serializers.ReviewPatchSerializer

    def perform_create(self, serializer):
        """
        Assigns authenticated user to the review instance.
        """
        photo = Photo.objects.get(id=self.kwargs["photo_id"])
        serializer.save(author=self.request.user, photo=photo)


class IsAuthor(permissions.BasePermission):
    """
    Grants author object permission.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
