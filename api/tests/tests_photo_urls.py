import os
from PIL import Image
from io import BytesIO
from rest_framework.test import APIClient, APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status

from ..models import Photo
from ..serializers import (
    PhotoCreateSerializer,
    PhotoDetailSerializer,
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


class PhotoCreateTestCase(APITestCase):
    def setUp(self) -> None:
        u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.image = create_image()
        self.data = {
            "image": self.image,
            "title": "test title",
            "description": "test description",
        }
        self.user = APIClient()
        self.user.force_authenticate(user=u)
        self.url = "/api/photos/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_create_photo(self):
        r = self.user.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Photo.objects.count(), 1)
        p = Photo.objects.first()
        self.assertEqual(p.author.username, "testUser")

    def test_missing_image(self):
        self.data.pop("image", None)
        r = self.user.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_title(self):
        self.data.pop("title", None)
        r = self.user.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_optional_description(self):
        self.data.pop("description", None)
        r = self.user.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_unauthorized_request(self):
        r = self.client.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class PhotoListTestCase(APITestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        for id in range(5):
            Photo.objects.create(
                author=self.u,
                image=create_image(),
                title=f"test title {id}",
                description=f"test description {id}",
            )
        self.url = "/api/photos/"

    def tearDown(self) -> None:
        for id in range(5):
            if os.path.isfile(f"media/photos/test_title_{id}.png"):
                os.remove(f"media/photos/test_title_{id}.png")

    def test_qs_returned(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        photos = Photo.objects.all()
        expected_data = PhotoDetailSerializer(photos, many=True).data

        for inst in r.data:
            for key, val in inst.items():
                if key == "image":
                    val = val.replace("http://testserver", "")
                    inst[key] = val

        self.assertEqual(r.data, expected_data)


class PhotoDeleteTestCase(APITestCase):
    def setUp(self) -> None:
        author = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        non_author = User.objects.create_user(
            username="testUser2",
            email="testemail2@test.com",
            password="test2password123",
        )
        self.p = Photo.objects.create(
            author=author,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.author = APIClient()
        self.author.force_authenticate(user=author)
        self.non_author = APIClient()
        self.non_author.force_authenticate(user=non_author)
        self.url = "/api/photos/"

    def test_author_can_delete(self):
        url = f"{self.url}{self.p.id}/"
        r = self.author.delete(url)
        self.assertNotEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.isfile("media/photos/test_title.png"))

    def test_non_author_cant_delete(self):
        url = f"{self.url}{self.p.id}/"
        r = self.non_author.delete(url)
        self.assertNotEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_delete_after_patch(self):
        url = f"{self.url}{self.p.id}/"
        data = {"title": "new title"}
        self.author.patch(url, data)
        r = self.author.delete(url)
        self.assertNotEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.isfile("media/photos/new_title.png"))


class PhotoRetrieveTestCase(APITestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.p = Photo.objects.create(
            author=self.u,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.url = f"/api/photos/{self.p.id}/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_qs_returned(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        p = Photo.objects.first()
        expected_data = PhotoDetailSerializer(p).data

        for key, val in r.data.items():
            if key == "image":
                val = val.replace("http://testserver", "")
                r.data[key] = val

        self.assertEqual(r.data, expected_data)

    def test_photo_not_found(self):
        r = self.client.get("/api/photos/99/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class PhotoUpdateTestCase(APITestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.p = Photo.objects.create(
            author=self.u,
            image=create_image(),
            title="test title",
            description="test description",
        )
        self.data = {
            "title": "new title",
            "description": "new description",
        }
        self.url = f"/api/photos/{self.p.id}/"
        self.author = APIClient()
        self.author.force_authenticate(user=self.u)

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/new_title.png"):
            os.remove("media/photos/new_title.png")
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_put_not_allowed(self):
        r = self.author.put(self.url)
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_works(self):
        r = self.author.patch(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.p.refresh_from_db()
        self.assertEqual(self.p.title, "new title")
        self.assertEqual(self.p.description, "new description")
        self.assertFalse(os.path.isfile("media/photos/test_title.png"))
        self.assertTrue(os.path.isfile("media/photos/new_title.png"))
