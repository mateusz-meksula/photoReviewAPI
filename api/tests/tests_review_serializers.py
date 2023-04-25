import os
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..serializers import (
    ReviewCreateSerializer,
    ReviewDetailSerializer,
    ReviewListSerializer,
    ReviewPatchSerializer,
)
from ..models import Photo, Review


User = get_user_model()


def create_image():
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = BytesIO()
    image.save(image_file, "png")
    image_file.seek(0)
    return SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png"
    )


class ReviewCreateSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.data = {
            "rating": 4,
            "body": "good test photo",
        }

    def test_serializer_is_valid(self):
        s = ReviewCreateSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_body(self):
        self.data.pop("body", None)
        s = ReviewCreateSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_rating_required(self):
        self.data.pop("rating", None)
        s = ReviewCreateSerializer(data=self.data)
        self.assertFalse(s.is_valid())


class ReviewDetailSerializerTestCase(TestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
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
            author=u,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good test photo",
        )

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_serializer_returns_expected_data(self):
        s = ReviewDetailSerializer(
            instance=self.review,
            context={"request": None},
        )
        expected_data = {
            "id": self.review.id,
            "author": "reviewer",
            "rating": 4,
            "body": "good test photo",
            "created_at": self.review.created_at.strftime("%d.%m.%Y %H:%M:%S"),
            "updated_at": None,
            "photo": f"/api/photos/{self.p.id}/",
        }
        self.assertEqual(s.data, expected_data)


class ReviewListSerializerTestCase(TestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
            username="testUser",
            email="test@test.com",
            password="testpassword123",
        )
        reviewer1 = User.objects.create_user(
            username="reviewer1",
            email="review1@review.com",
            password="review1123",
        )
        reviewer2 = User.objects.create_user(
            username="reviewer2",
            email="review2@review.com",
            password="review2123",
        )
        self.p = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.review1 = Review.objects.create(
            author=reviewer1,
            photo=self.p,
            rating=4,
            body="good test photo",
        )
        self.review2 = Review.objects.create(
            author=reviewer2,
            photo=self.p,
            rating=5,
            body="very good test photo",
        )

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_serializer_returns_expected_data(self):
        reviews = Review.objects.all()
        s = ReviewListSerializer(reviews, many=True, context={"request": None})
        expected_data = [
            {
                "id": self.review1.id,
                "url": f"/api/photos/{self.p.id}/reviews/{self.review1.id}/",
                "author": "reviewer1",
                "rating": 4,
                "body": "good test photo",
            },
            {
                "id": self.review2.id,
                "url": f"/api/photos/{self.p.id}/reviews/{self.review2.id}/",
                "author": "reviewer2",
                "rating": 5,
                "body": "very good test photo",
            },
        ]
        self.assertEqual(s.data, expected_data)


class ReviewPatchSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.data = {
            "rating": 2,
            "body": "bad test photo",
        }

    def test_serializer_is_valid(self):
        s = ReviewPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_body(self):
        self.data.pop("body", None)
        s = ReviewPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())

    def test_optional_rating(self):
        self.data.pop("rating", None)
        s = ReviewPatchSerializer(data=self.data)
        self.assertTrue(s.is_valid())
