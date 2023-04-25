import os
from PIL import Image
from io import BytesIO
from django.db.models import Avg
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Photo, Review, Tag
from ..serializers import (
    PhotoCreateSerializer,
    PhotoDetailSerializer,
    PhotoListSerializer,
    PhotoPatchSerializer,
)


User = get_user_model()


def create_image():
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = BytesIO()
    image.save(image_file, "png")
    image_file.seek(0)
    return SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png"
    )


class PhotoCreateSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.data = {
            "image": create_image(),
            "title": "test photo",
            "description": "test description",
        }

    def test_serializer_is_valid(self):
        s = PhotoCreateSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_missing_image(self):
        self.data.pop("image", None)
        s = PhotoCreateSerializer(data=self.data)
        self.assertFalse(s.is_valid())

    def test_missing_title(self):
        self.data.pop("title", None)
        s = PhotoCreateSerializer(data=self.data)
        self.assertFalse(s.is_valid())

    def test_optional_description(self):
        self.data.pop("description", None)
        s = PhotoCreateSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_serializer_is_valid_with_tags(self):
        self.data["tags"] = ["DRF", "test", "django"]
        s = PhotoCreateSerializer(data=self.data)
        self.assertTrue(s.is_valid())


class PhotoDetailSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="test@test.com",
            password="testpassword123",
        )
        reviewer = User.objects.create_user(
            username="reviewer",
            email="review@review.com",
            password="review123",
        )
        self.p = Photo.objects.create(
            author=self.u,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.t = Tag.objects.create(name="test")
        self.p.tags.add(self.t)
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good test photo",
        )
        self.qs = Photo.objects.annotate(average_rating=Avg("reviews__rating"))

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_serializer_returns_expected_data(self):
        inst = self.qs.get(id=self.p.id)
        s = PhotoDetailSerializer(instance=inst, context={"request": None})
        expected_data = {
            "id": self.p.id,
            "author": "testUser",
            "title": "test title",
            "image": "/media/photos/test_title.png",
            "description": "test description",
            "average_rating": 4.0,
            "created_at": self.p.created_at.strftime("%d.%m.%Y %H:%M:%S"),
            "updated_at": None,
            "tags": ["test"],
            "reviews": [f"/api/photos/{self.p.id}/reviews/{self.review.id}/"],
        }
        self.assertEqual(s.data, expected_data)


class PhotoListSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="test@test.com",
            password="testpassword123",
        )
        self.p1 = Photo.objects.create(
            author=self.u,
            image=create_image(),
            title="test title 1",
            description="test description 1",
        )
        self.p2 = Photo.objects.create(
            author=self.u,
            image=create_image(),
            title="test title 2",
            description="test description 2",
        )
        self.qs = Photo.objects.annotate(average_rating=Avg("reviews__rating"))

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title_1.png"):
            os.remove("media/photos/test_title_1.png")
        if os.path.isfile("media/photos/test_title_2.png"):
            os.remove("media/photos/test_title_2.png")

    def test_serializer_returns_expected_data(self):
        s = PhotoListSerializer(
            self.qs,
            many=True,
            context={"request": None},
        )
        expected_data = [
            {
                "id": self.p2.id,
                "url": f"/api/photos/{self.p2.id}/",
                "author": "testUser",
                "title": "test title 2",
                "image": "/media/photos/test_title_2.png",
                "average_rating": None,
            },
            {
                "id": self.p1.id,
                "url": f"/api/photos/{self.p1.id}/",
                "author": "testUser",
                "title": "test title 1",
                "image": "/media/photos/test_title_1.png",
                "average_rating": None,
            },
        ]

        self.assertEqual(s.data, expected_data)


class PhotoPatchSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.data = {
            "title": "new test title",
            "description": "new test description",
            "tags": ["new", "drf"],
        }

    def test_serializer_is_valid(self):
        s = PhotoPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_title(self):
        self.data.pop("title", None)
        s = PhotoPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_description(self):
        self.data.pop("description", None)
        s = PhotoPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_tags(self):
        self.data.pop("tags", None)
        s = PhotoPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())
