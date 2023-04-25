from django.contrib import admin

from .models import Photo, Review, Tag


admin.site.register(Photo)
admin.site.register(Review)
admin.site.register(Tag)
