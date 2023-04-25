from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


urlpatterns = [
    # sign-up, account activation, password reset
    path("auth/", include("flash_accounts.urls")),
    # jwt
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# photos and tags urls
router = SimpleRouter()
router.register(r"photos", views.PhotoViewSet, basename="photo")
router.register(r"tags", views.TagViewSet, basename="tag")
urlpatterns += router.urls

# reviews urls, nested with photos urls
reviews_router = SimpleRouter()
reviews_router.register("reviews", views.ReviewViewSet, basename="review")
urlpatterns += [path("photos/<int:photo_id>/", include(reviews_router.urls))]
