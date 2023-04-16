from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # api endpoints
    path("api/", include("api.urls")),
]
