from django.urls import path

from .api_views import (
    CreateFeedPostAPIView,
    FeedAPIView,
    UpdatePostAPIView,
    DeletePostAPIView,
    ToggleLikePostAPIView,
    CommunityListAPIView,
    CreateCommunityAPIView,
    CommunityDetailAPIView,
    CreateCommunityPostAPIView,
    JoinCommunityAPIView,
    LeaveCommunityAPIView,
    UpdateCommunityAPIView,
    DeleteCommunityAPIView,
    CreateCommentAPIView,
    ReplyCommentAPIView,
    UpdateCommentAPIView,
    DeleteCommentAPIView,
    ToggleLikeCommentAPIView,
)

# =====================================
# ROTAS DA API DE POSTS / COMUNIDADES
# =====================================
urlpatterns = [
    # ------------------------------
    # FEED GLOBAL
    # ------------------------------
    # GET  /api/posts/feed/
    path("feed/", FeedAPIView.as_view(), name="feed"),

    # ------------------------------
    # CRIAR POST NO FEED
    # ------------------------------
    # POST /api/posts/feed/create/
    path("feed/create/", CreateFeedPostAPIView.as_view(), name="create-feed-post"),

    # ------------------------------
    # EDITAR / EXCLUIR / CURTIR POST
    # ------------------------------
    # PUT/PATCH /api/posts/post/<post_id>/update/
    path("post/<int:post_id>/update/", UpdatePostAPIView.as_view(), name="update-post"),

    # DELETE /api/posts/post/<post_id>/delete/
    path("post/<int:post_id>/delete/", DeletePostAPIView.as_view(), name="delete-post"),

    # POST /api/posts/post/<post_id>/like/
    path("post/<int:post_id>/like/", ToggleLikePostAPIView.as_view(), name="toggle-like-post"),

    # ------------------------------
    # COMUNIDADES
    # ------------------------------
    # GET /api/posts/communities/
    path("communities/", CommunityListAPIView.as_view(), name="communities"),

    # POST /api/posts/communities/create/
    path("communities/create/", CreateCommunityAPIView.as_view(), name="create-community"),

    # GET /api/posts/communities/<slug>/
    path("communities/<slug:slug>/", CommunityDetailAPIView.as_view(), name="community-detail"),

    # POST /api/posts/communities/<slug>/post/create/
    path(
        "communities/<slug:slug>/post/create/",
        CreateCommunityPostAPIView.as_view(),
        name="create-community-post",
    ),

    # POST /api/posts/communities/<slug>/join/
    path("communities/<slug:slug>/join/", JoinCommunityAPIView.as_view(), name="join-community"),

    # POST /api/posts/communities/<slug>/leave/
    path("communities/<slug:slug>/leave/", LeaveCommunityAPIView.as_view(), name="leave-community"),

    # PUT/PATCH /api/posts/communities/<slug>/update/
    path(
        "communities/<slug:slug>/update/",
        UpdateCommunityAPIView.as_view(),
        name="update-community",
    ),

    # DELETE /api/posts/communities/<slug>/delete/
    path(
        "communities/<slug:slug>/delete/",
        DeleteCommunityAPIView.as_view(),
        name="delete-community",
    ),

    # ------------------------------
    # COMENTÁRIOS
    # ------------------------------
    # POST /api/posts/post/<post_id>/comment/
    path(
        "post/<int:post_id>/comment/",
        CreateCommentAPIView.as_view(),
        name="create-comment",
    ),

    # POST /api/posts/comment/<comment_id>/reply/
    path(
        "comment/<int:comment_id>/reply/",
        ReplyCommentAPIView.as_view(),
        name="reply-comment",
    ),

    # PUT/PATCH /api/posts/comment/<comment_id>/update/
    path(
        "comment/<int:comment_id>/update/",
        UpdateCommentAPIView.as_view(),
        name="update-comment",
    ),

    # DELETE /api/posts/comment/<comment_id>/delete/
    path(
        "comment/<int:comment_id>/delete/",
        DeleteCommentAPIView.as_view(),
        name="delete-comment",
    ),

    # POST /api/posts/comment/<comment_id>/like/
    path(
        "comment/<int:comment_id>/like/",
        ToggleLikeCommentAPIView.as_view(),
        name="toggle-like-comment",
    ),
]