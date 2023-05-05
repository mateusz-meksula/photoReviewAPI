from rest_framework import filters
from django.db.models import Avg, Count
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from . import serializers
from .models import Photo, Tag


class PhotoViewSet(ModelViewSet):
    """
    ViewSet for Photo instances management.
    """

    # exclude `put` HTTP method
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]

    queryset = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "description", "author__username", "tags__name"]
    ordering_fields = ["created_at", "average_rating", "title"]
    ordering = ["-created_at"]
    filterset_fields = ["created_at", "updated_at", "id", "author__username", "title", "tags__name"]

    def get_permissions(self):
        """
        Sets permission depending on the action.
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
        Sets serializer class depending on the action.
        """

        if self.action == "create":
            return serializers.PhotoCreateSerializer
        if self.action == "list":
            return serializers.PhotoListSerializer
        if self.action in ("retrieve", "destroy"):
            return serializers.PhotoDetailSerializer
        if self.action == "partial_update":
            return serializers.PhotoPatchSerializer

    def perform_create(self, serializer):
        """
        Assigns authenticated user to the photo instance.
        """
        serializer.save(author=self.request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Limits results if 'limit' query parameter is given.
        """

        limit = self.request.query_params.get("limit")
        if limit:
            response.data = response.data[: int(limit)]
        return super().finalize_response(request, response, *args, **kwargs)


class TagViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for Tag instances.
    """

    queryset = Tag.objects.annotate(number_of_photos=Count("photos"))
    serializer_class = serializers.TagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["name", "photos__title"]
    ordering_fields = ["name", "number_of_photos"]
    ordering = ["-number_of_photos", "name"]
    filterset_fields = ["id", "name", "photos__title"]
    lookup_field = "name"

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Limits results if 'limit' query parameter is given.
        """

        limit = self.request.query_params.get("limit")
        if limit:
            response.data = response.data[: int(limit)]
        return super().finalize_response(request, response, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    """
    ViewSet for Review instances management.
    """

    # exclude `put` HTTP method
    http_method_names = [m for m in ModelViewSet.http_method_names if m != "put"]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["created_at", "rating"]
    ordering = ["-created_at"]
    filterset_fields = ["created_at", "updated_at", "id", "author__username", "rating"]

    def get_queryset(self):
        """
        Returns reviews of photo related to a given `photo_id` in the url.
        """

        photo = get_object_or_404(Photo, pk=self.kwargs["photo_id"])
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
        Returns 403 if user tries to review his own photo.
        Returns 404 if user tries to review same photo twice.
        """

        photo = get_object_or_404(Photo, pk=self.kwargs["photo_id"])
        if self.request.user == photo.author:
            raise PermissionDenied()
        if photo.reviews.filter(author=self.request.user):
            raise PermissionDenied()

        serializer.save(author=self.request.user, photo=photo)


class IsAuthor(permissions.BasePermission):
    """
    Custom `BasePermission`.
    Grants the author an object permission.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
