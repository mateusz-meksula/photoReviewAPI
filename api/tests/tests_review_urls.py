import os
from PIL import Image
from io import BytesIO
from rest_framework.test import APIClient, APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status

from ..models import Photo, Review

from ..serializers import ReviewListSerializer, ReviewDetailSerializer

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

    def test_reviewer_cant_review_twice(self):
        self.reviewer.post(self.url, self.data)
        self.data["rating"] = 2
        self.data["body"] = "bad photo"
        r = self.reviewer.post(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class ReviewListTestCase(APITestCase):
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
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good photo",
        )
        self.url = f"/api/photos/{self.p.id}/reviews/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_qs_returned(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        reviews = self.p.reviews.all()
        expected_data = ReviewListSerializer(
            reviews, many=True, context={"request": None}
        ).data
        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))


class ReviewDeleteTestCase(APITestCase):
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
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good photo",
        )
        self.url = f"/api/photos/{self.p.id}/reviews/{self.review.id}/"
        self.reviewer = APIClient()
        self.reviewer.force_authenticate(user=reviewer)
        self.user = APIClient()
        self.user.force_authenticate(user=u)

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_author_can_delete(self):
        r = self.reviewer.delete(self.url)
        self.assertNotEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)

    def test_non_author_cant_delete(self):
        r = self.user.delete(self.url)
        self.assertNotEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.count(), 1)


class ReviewRetrieveTestCase(APITestCase):
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
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good photo",
        )
        self.url = f"/api/photos/{self.p.id}/reviews/{self.review.id}/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_qs_returned(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        review = Review.objects.first()
        expected_data = ReviewDetailSerializer(
            review,
            context={"request": None},
        ).data
        data_str = str(r.data).replace("http://testserver", "")
        self.assertEqual(data_str, str(expected_data))

    def test_review_not_found(self):
        r = self.client.get(f"/api/photos/{self.p.id}/reviews/99/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class ReviewUpdateTestCase(APITestCase):
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
        self.review = Review.objects.create(
            author=reviewer,
            photo=self.p,
            rating=4,
            body="good photo",
        )
        self.data = {"rating": 2, "body": "bad test photo"}
        self.reviewer = APIClient()
        self.reviewer.force_authenticate(user=reviewer)
        # self.author = APIClient()
        # self.author.force_authenticate(user=u)
        self.url = f"/api/photos/{self.p.id}/reviews/{self.review.id}/"

    def tearDown(self) -> None:
        if os.path.isfile("media/photos/test_title.png"):
            os.remove("media/photos/test_title.png")

    def test_patch_works(self):
        r = self.reviewer.patch(self.url, self.data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 2)
        self.assertEqual(self.review.body, "bad test photo")
