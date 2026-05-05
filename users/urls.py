from django.urls import path
from .api_views import (
    RegisterAPIView,
    MyProfileAPIView,
    UpdateMyProfileAPIView,
    PublicProfileAPIView,
    FriendsListAPIView,
    ReceivedFriendRequestsAPIView,
    SentFriendRequestsAPIView,
    SendFriendRequestAPIView,
    CancelFriendRequestAPIView,
    AcceptFriendRequestAPIView,
    RejectFriendRequestAPIView,
    RemoveFriendAPIView,
)

# =====================================
# ROTAS DA API DE USUÁRIOS
# =====================================
urlpatterns = [
    
    # CADASTRO
    # ------------------------------
    # POST /api/users/register/
    path("register/", RegisterAPIView.as_view(), name="register"),

    # ------------------------------
    # PERFIL DO USUÁRIO LOGADO
    # ------------------------------
    # GET /api/users/me/
    path("me/", MyProfileAPIView.as_view(), name="my-profile"),

    # ------------------------------
    # EDIÇÃO DO PERFIL DO USUÁRIO LOGADO
    # ------------------------------
    # PUT/PATCH /api/users/me/update/
    path("me/update/", UpdateMyProfileAPIView.as_view(), name="update-my-profile"),

    # ------------------------------
    # PERFIL PÚBLICO
    # ------------------------------
    # GET /api/users/profile/<nickname>/
    path("profile/<str:nickname>/", PublicProfileAPIView.as_view(), name="public-profile"),

    # ------------------------------
    # AMIGOS
    # ------------------------------
    # GET /api/users/friends/
    path("friends/", FriendsListAPIView.as_view(), name="friends-list"),

    # ------------------------------
    # SOLICITAÇÕES DE AMIZADE
    # ------------------------------
    # GET /api/users/friend-requests/received/
    path(
        "friend-requests/received/",
        ReceivedFriendRequestsAPIView.as_view(),
        name="received-friend-requests",
    ),

    # GET /api/users/friend-requests/sent/
    path(
        "friend-requests/sent/",
        SentFriendRequestsAPIView.as_view(),
        name="sent-friend-requests",
    ),

    # POST /api/users/friend-request/<nickname>/send/
    path(
        "friend-request/<str:nickname>/send/",
        SendFriendRequestAPIView.as_view(),
        name="send-friend-request",
    ),

    # POST /api/users/friend-request/<nickname>/cancel/
    path(
        "friend-request/<str:nickname>/cancel/",
        CancelFriendRequestAPIView.as_view(),
        name="cancel-friend-request",
    ),

    # POST /api/users/friend-request/<nickname>/accept/
    path(
        "friend-request/<str:nickname>/accept/",
        AcceptFriendRequestAPIView.as_view(),
        name="accept-friend-request",
    ),

    # POST /api/users/friend-request/<nickname>/reject/
    path(
        "friend-request/<str:nickname>/reject/",
        RejectFriendRequestAPIView.as_view(),
        name="reject-friend-request",
    ),

    # ------------------------------
    # REMOVER AMIGO
    # ------------------------------
    # POST /api/users/friend/<nickname>/remove/
    path(
        "friend/<str:nickname>/remove/",
        RemoveFriendAPIView.as_view(),
        name="remove-friend",
    ),
]