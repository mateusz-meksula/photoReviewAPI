import os
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from ..models import Photo, Tag
from ..serializers import TagDetailSerializer, TagListSerializer

User = get_user_model()


def create_image():
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = BytesIO()
    image.save(image_file, "png")
    image_file.seek(0)
    return SimpleUploadedFile(
        "test_image.png", image_file.read(), content_type="image/png"
    )


class TagUrlsTestCase(APITestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.t1 = Tag.objects.create(name="drf")
        t2 = Tag.objects.create(name="test")
        t3 = Tag.objects.create(name="django")
        p1 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 0",
            description="test description 0",
        )
        p2 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 1",
            description="test description 1",
        )
        p3 = Photo.objects.create(
            author=u,
            image=create_image(),
            title="test title 2",
            description="test description 2",
        )
        p1.tags.add(self.t1, t2)
        p2.tags.add(self.t1)
        self.url = "/api/tags/"

    def tearDown(self) -> None:
        for id in range(3):
            if os.path.isfile(f"media/photos/test_title_{id}.png"):
                os.remove(f"media/photos/test_title_{id}.png")

    def test_list_tags(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        tags = Tag.objects.all()
        expected_data = TagListSerializer(
            tags, many=True, context={"request": None}
        ).data

        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

    def test_retrieve_tag(self):
        url = f"{self.url}{self.t1.name}/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        expected_data = TagDetailSerializer(
            self.t1,
            context={"request": None},
        ).data
        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

    def test_tag_not_found(self):
        url = f"{self.url}none/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
