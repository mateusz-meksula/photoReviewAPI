from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


urlpatterns = [
    # sign-up, account activation, password reset
    path("auth/", include("flash_accounts.urls")),
    # jwt
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# models urls
router = DefaultRouter()
router.register(r"photos", views.PhotoViewSet, basename="photo")
urlpatterns += router.urls
