import os
from PIL import Image
from io import BytesIO
from rest_framework.test import APIClient, APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status

from ..models import Photo, Review

# from ..serializers import PhotoDetailSerializer, PhotoListSerializer

User = get_user_model()


def create_image():
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = BytesIO()
    image.save(image_file, "png")
    image_file.seek(0)
    return SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png"
    )


class ReviewCreateTestCase(APITestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        reviewer = User.objects.create_user(
            username="reviewer",
            email="reviewer@test.com",
            password="reviewer123",
        )
        self.p = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title",
            description="test",
        )
        self.data = {"rating": 4, "body": "nice test photo"}
        self.reviewer = APIClient()
        self.reviewer.force_authenticate(user=reviewer)
        self.author = APIClient()
        self.author.force_authenticate(user=u)
        self.url = f"/api/photos/{self.p.id}/reviews/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_create_review(self):
        r = self.reviewer.post(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        rev = Review.objects.first()
        self.assertEqual(rev.rating, 4)
        self.assertEqual(rev.body, "nice test photo")
        self.assertEqual(rev.photo, self.p)

    def test_missing_rating(self):
        self.data.pop("rating", None)
        r = self.reviewer.post(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_optional_body(self):
        self.data.pop("body", None)
        r = self.reviewer.post(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_author_cant_review(self):
        r = self.author.post(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.count(), 0)
