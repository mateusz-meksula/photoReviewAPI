import os
from PIL import Image
from io import BytesIO
from django.db.models import Avg
from rest_framework.test import APIClient, APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status

from ..models import Photo, Tag, Review
from ..serializers import PhotoDetailSerializer, PhotoListSerializer

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
            "tags": [
                "drf",
                "test",
            ],
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
        self.assertEqual(p.title, "test title")
        self.assertTrue(os.path.isfile("media/photos/test_title.png"))
        self.assertEqual(p.description, "test description")
        self.assertEqual(Tag.objects.count(), 2)
        self.assertEqual(p.tags.count(), 2)
        self.assertQuerysetEqual(
            Tag.objects.all(),
            p.tags.all(),
            ordered=False,
        )

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

    def test_optional_tags(self):
        self.data.pop("tags", None)
        r = self.user.post(self.url, self.data, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 0)

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
        self.t = Tag.objects.create(name="test")
        for id in range(5):
            p = Photo.objects.create(
                author=self.u,
                image=create_image(),
                title=f"test title {id}",
                description=f"test description {id}",
            )
            p.tags.add(self.t)
        self.url = "/api/photos/"

    def tearDown(self) -> None:
        for id in range(5):
            if os.path.isfile(f"media/photos/test_title_{id}.png"):
                os.remove(f"media/photos/test_title_{id}.png")

    def test_qs_returned(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        photos = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
        expected_data = PhotoListSerializer(
            photos, many=True, context={"request": None}
        ).data

        data = sorted(r.data, key=lambda inst: inst["id"])
        data_str = str(data).replace("http://testserver", "")
        expected_data = sorted(expected_data, key=lambda inst: inst["id"])

        self.assertEqual(data_str, str(expected_data))


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
        t = Tag.objects.create(name="test")
        self.p.tags.add(t)
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
        self.assertEqual(Photo.objects.count(), 0)

    def test_non_author_cant_delete(self):
        url = f"{self.url}{self.p.id}/"
        r = self.non_author.delete(url)
        self.assertNotEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Photo.objects.count(), 1)

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
        self.assertEqual(Photo.objects.count(), 0)

    def test_tag_not_deleted(self):
        self.assertEqual(Tag.objects.count(), 1)
        url = f"{self.url}{self.p.id}/"
        self.author.delete(url)
        self.assertEqual(Tag.objects.count(), 1)


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
        qs = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
        p = qs.first()
        expected_data = PhotoDetailSerializer(p).data

        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

    def test_qs_returned_with_tags(self):
        qs = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
        p = qs.first()
        t1 = Tag.objects.create(name="drf")
        t2 = Tag.objects.create(name="test")
        p.tags.add(t1, t2)

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        expected_data = PhotoDetailSerializer(p).data
        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

    def test_qs_returned_with_reviews(self):
        u = User.objects.create_user(
            username="reviewer",
            email="reviewer@test.com",
            password="reviewer123",
        )
        Review.objects.create(
            author=u,
            photo=self.p,
            rating=4,
            body="Good photo",
        )
        # self.p.refresh_from_db()
        qs = Photo.objects.annotate(average_rating=Avg("reviews__rating"))
        p = qs.first()

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        expected_data = PhotoDetailSerializer(
            p,
            context={"request": None},
        ).data
        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

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
            "tags": ["new", "test"],
        }
        self.t1 = Tag.objects.create(name="test")
        self.t2 = Tag.objects.create(name="drf")
        self.p.tags.add(self.t1, self.t2)
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

    def test_patch_works_without_tags(self):
        self.p.tags.clear()
        self.data.pop("tags", None)
        r = self.author.patch(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.p.refresh_from_db()
        self.assertEqual(self.p.title, "new title")
        self.assertEqual(self.p.description, "new description")
        self.assertEqual(self.p.tags.count(), 0)
        self.assertFalse(os.path.isfile("media/photos/test_title.png"))
        self.assertTrue(os.path.isfile("media/photos/new_title.png"))

    def test_patch_works_with_tags(self):
        r = self.author.patch(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.p.refresh_from_db()
        self.assertEqual(self.p.title, "new title")
        self.assertEqual(self.p.description, "new description")
        self.assertEqual(self.p.tags.count(), 2)
        self.assertEqual(Tag.objects.count(), 3)
        t = Tag.objects.get(name="new")
        self.assertIn(self.t1, self.p.tags.all())
        self.assertIn(t, self.p.tags.all())
        self.assertNotIn(self.t2, self.p.tags.all())
        self.assertFalse(os.path.isfile("media/photos/test_title.png"))
        self.assertTrue(os.path.isfile("media/photos/new_title.png"))
