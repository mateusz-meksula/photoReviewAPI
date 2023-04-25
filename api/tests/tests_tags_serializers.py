import os
from PIL import Image
from io import BytesIO
from django.db.models import Count
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Photo, Tag
from ..serializers import TagSerializer


User = get_user_model()


def create_image():
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = BytesIO()
    image.save(image_file, "png")
    image_file.seek(0)
    return SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png"
    )


class TagSerializerTestCase(TestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="password123",
        )
        self.p1 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 1",
            description="description 1",
        )
        self.p2 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 2",
            description="description 2",
        )
        self.p3 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 3",
            description="description 3",
        )
        self.t1 = Tag.objects.create(name="test")
        self.t2 = Tag.objects.create(name="django")
        self.t3 = Tag.objects.create(name="drf")
        self.t4 = Tag.objects.create(name="REST")

        self.p1.tags.add(self.t1, self.t2, self.t3, self.t4)
        self.p2.tags.add(self.t1, self.t4)
        self.p3.tags.add(self.t4)

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title_1.png"):
            os.remove("media/photos/test_title_1.png")
        if os.path.isfile("media/photos/test_title_2.png"):
            os.remove("media/photos/test_title_2.png")
        if os.path.isfile("media/photos/test_title_3.png"):
            os.remove("media/photos/test_title_3.png")

    def test_serializer_returns_expected_data(self):
        tags = Tag.objects.annotate(number_of_photos=Count("photos"))
        s = TagSerializer(tags, many=True, context={"request": None})
        expected_data = [
            {
                "id": self.t4.id,
                "name": "REST",
                "number_of_photos": 3,
                "photos": [
                    f"/api/photos/{self.p1.id}/",
                    f"/api/photos/{self.p2.id}/",
                    f"/api/photos/{self.p3.id}/",
                ],
            },
            {
                "id": self.t2.id,
                "name": "django",
                "number_of_photos": 1,
                "photos": [
                    f"/api/photos/{self.p1.id}/",
                ],
            },
            {
                "id": self.t3.id,
                "name": "drf",
                "number_of_photos": 1,
                "photos": [
                    f"/api/photos/{self.p1.id}/",
                ],
            },
            {
                "id": self.t1.id,
                "name": "test",
                "number_of_photos": 2,
                "photos": [
                    f"/api/photos/{self.p1.id}/",
                    f"/api/photos/{self.p2.id}/",
                ],
            },
        ]

        self.assertEqual(s.data, expected_data)
