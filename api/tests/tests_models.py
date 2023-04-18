import os

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models import Photo, Tag

User = get_user_model()


class PhotoTestCase(TestCase):
    def setUp(self) -> None:
        self.u = User.objects.create_user(
            username="testUser",
            email="testemail@test.com",
            password="testpassword123",
        )
        self.image = SimpleUploadedFile(
            name="test_image.jpg", content=b"", content_type="image/jpg"
        )
        self.photo = Photo.objects.create(
            author=self.u,
            image=self.image,
            title="test title",
            description="test description",
        )

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.jpg"):
            os.remove("media/photos/test_title.jpg")

    def test_photo_fields(self):
        self.assertEqual(self.u, self.photo.author)
        self.assertEqual("test title", self.photo.title)
        self.assertEqual("test description", self.photo.description)

    def test_image_uploaded(self):
        self.assertTrue(os.path.isfile("media/photos/test_title.jpg"))

    def test_photo_url(self):
        self.assertEqual(self.photo.image.url, f"/media/{self.photo.image.name}")

    def test_image_too_big(self):
        image_size = 3 * 1024 * 1024 + 1
        image_content = b"a" * image_size
        image = SimpleUploadedFile(
            name="big_image.jpg", content=image_content, content_type="image/jpg"
        )
        photo = Photo(author=self.u, image=image, title="test", description="test")

        self.assertRaises(ValidationError, photo.full_clean)


class TagTestCase(TestCase):
    def setUp(self) -> None:
        self.t = Tag.objects.create(name="test")

    def test_tag_created(self):
        self.assertEqual(Tag.objects.count(), 1)
        t = Tag.objects.first()
        self.assertEqual(t.name, "test")
        self.assertEqual(t.__str__(), "test")

    def test_tag_name_validation(self):
        t1 = Tag(name=123)
        t2 = Tag(name="123")
        t3 = Tag(name="test12")
        t4 = Tag(name="test test")
        self.assertRaises(ValidationError, t1.full_clean)
        self.assertRaises(ValidationError, t2.full_clean)
        self.assertRaises(ValidationError, t3.full_clean)
        self.assertRaises(ValidationError, t4.full_clean)
