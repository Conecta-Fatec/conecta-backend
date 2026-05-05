from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "content", "created_at")
    search_fields = ("content", "author__nickname", "author__email")
    list_filter = ("created_at",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "content", "post", "parent", "created_at")
    search_fields = ("content", "author__nickname", "author__email")
    list_filter = ("created_at",)