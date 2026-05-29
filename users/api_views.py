from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import prefetch_related_objects

from .models import CustomUser, Friendship
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    PublicUserSerializer,
    ProfileUpdateSerializer,
    FriendshipSerializer,
    UserCardSerializer,
)


# =====================================
# CADASTRO DE USUÁRIO
# =====================================
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            response_serializer = UserSerializer(
                user,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Usuário cadastrado com sucesso.",
                    "user": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# =====================================
# PERFIL PRIVADO DO USUÁRIO LOGADO
# =====================================
class MyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Agora usamos os nomes EXATOS para blindar o N+1 de uma vez por todas
        user = CustomUser.objects.prefetch_related(
            'sent_friendships__receiver',
            'received_friendships__sender',
            'created_communities',
            'communities',
            'posts__community'  # <- Esta magia traz o nome da comunidade do post junto!
        ).get(id=request.user.id)

        serializer = UserSerializer(
            user,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

# =====================================
# EDIÇÃO DO PERFIL DO USUÁRIO LOGADO
# =====================================
class UpdateMyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.save()

            response_serializer = UserSerializer(
                user,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Perfil atualizado com sucesso.",
                    "user": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.save()

            response_serializer = UserSerializer(
                user,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Perfil atualizado com sucesso.",
                    "user": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# PERFIL PÚBLICO POR NICKNAME
# =====================================
class PublicProfileAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, nickname):
        user = get_object_or_404(CustomUser, nickname=nickname)

        serializer = PublicUserSerializer(
            user,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================
# BUSCAR / LISTAR USUÁRIOS
# =====================================
# Usado pela página de amizades.
# Retorna também o total real de usuários cadastrados no site.
class UsersSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = (
            request.query_params.get("q")
            or request.query_params.get("search")
            or ""
        ).strip()

        # O prefetch_related puxa todas as amizades de todos os usuários numa tacada só!
        users = CustomUser.objects.prefetch_related(
            "sent_friendships__receiver",
            "received_friendships__sender"
        ).all().order_by("first_name", "last_name", "nickname")

        if query:
            users = users.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(nickname__icontains=query)
                | Q(course__icontains=query)
            )

        serializer = UserCardSerializer(
            users,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "total_users": CustomUser.objects.count(),
                "count": users.count(),
                "users": serializer.data,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# TOTAL DE USUÁRIOS CADASTRADOS
# =====================================
class UsersTotalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"total_users": CustomUser.objects.count()},
            status=status.HTTP_200_OK
        )


# =====================================
# LISTAR AMIGOS DO USUÁRIO LOGADO
# =====================================
class FriendsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Carrega o usuário atual já com o cache de amizades
        user_with_prefetch = CustomUser.objects.prefetch_related(
            "sent_friendships__receiver",
            "received_friendships__sender"
        ).get(id=request.user.id)
        
        friends = user_with_prefetch.get_friends()

        data = [
            {
                "id": friend.id,
                "full_name": f"{friend.first_name} {friend.last_name}".strip(),
                "nickname": friend.nickname,
                "course": friend.course,
                "bio": friend.bio,
                "photo_url": (
                    request.build_absolute_uri(friend.photo.url)
                    if friend.photo
                    else None
                ),
            }
            for friend in friends
        ]

        return Response(
            {
                "friends_count": len(data),
                "friends": data,
            },
            status=status.HTTP_200_OK
        )



# =====================================
# LISTAR AMIGOS DE UM PERFIL PÚBLICO
# =====================================
class PublicFriendsListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, nickname):
        # 1. Pega o dono do perfil com prefetch
        user = CustomUser.objects.prefetch_related(
            "sent_friendships__receiver",
            "received_friendships__sender"
        ).get(nickname=nickname)
        
        friends = user.get_friends()

        # Carrega as amizades DE TODOS OS AMIGOS na memória numa única consulta!
        prefetch_related_objects(friends, "sent_friendships__receiver", "received_friendships__sender")

        serializer = UserCardSerializer(
            friends,
            many=True,
            context={"request": request}
        )
        
        return Response(
            {
                "nickname": user.nickname,
                "friends_count": len(friends),
                "count": len(friends),
                "friends": serializer.data,
            },
            status=status.HTTP_200_OK
        )

class ReceivedFriendRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_received = Friendship.objects.filter(
            receiver=request.user,
            status="pending"
        ).select_related("sender", "receiver").order_by("-created_at")

        serializer = FriendshipSerializer(
            requests_received,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "count": requests_received.count(),
                "requests": serializer.data,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# LISTAR SOLICITAÇÕES ENVIADAS
# =====================================
class SentFriendRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_sent = Friendship.objects.filter(
            sender=request.user,
            status="pending"
        ).select_related("sender", "receiver").order_by("-created_at")

        serializer = FriendshipSerializer(
            requests_sent,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "count": requests_sent.count(),
                "requests": serializer.data,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# ENVIAR SOLICITAÇÃO DE AMIZADE
# =====================================
class SendFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nickname):
        receiver = get_object_or_404(CustomUser, nickname=nickname)
        sender = request.user

        if sender == receiver:
            return Response(
                {"detail": "Você não pode enviar solicitação para si mesmo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sender.is_friends_with(receiver):
            return Response(
                {"detail": "Vocês já são amigos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sender.sent_friend_request_to(receiver):
            return Response(
                {"detail": "Você já enviou uma solicitação para este usuário."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sender.received_friend_request_from(receiver):
            return Response(
                {
                    "detail": "Este usuário já enviou uma solicitação para você. "
                              "Aceite a solicitação recebida."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        friendship = Friendship.objects.create(
            sender=sender,
            receiver=receiver,
            status="pending"
        )

        serializer = FriendshipSerializer(
            friendship,
            context={"request": request}
        )

        return Response(
            {
                "message": "Solicitação de amizade enviada com sucesso.",
                "friendship": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )


# =====================================
# CANCELAR SOLICITAÇÃO ENVIADA
# =====================================
class CancelFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nickname):
        receiver = get_object_or_404(CustomUser, nickname=nickname)

        friendship = Friendship.objects.filter(
            sender=request.user,
            receiver=receiver,
            status="pending"
        ).first()

        if not friendship:
            return Response(
                {"detail": "Nenhuma solicitação pendente enviada para este usuário."},
                status=status.HTTP_404_NOT_FOUND
            )

        friendship.delete()

        return Response(
            {"message": "Solicitação de amizade cancelada com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# ACEITAR SOLICITAÇÃO RECEBIDA
# =====================================
class AcceptFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nickname):
        sender = get_object_or_404(CustomUser, nickname=nickname)

        friendship = Friendship.objects.filter(
            sender=sender,
            receiver=request.user,
            status="pending"
        ).first()

        if not friendship:
            return Response(
                {"detail": "Nenhuma solicitação pendente deste usuário foi encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        friendship.status = "accepted"
        friendship.save()

        serializer = FriendshipSerializer(
            friendship,
            context={"request": request}
        )

        return Response(
            {
                "message": "Solicitação de amizade aceita com sucesso.",
                "friendship": serializer.data,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# RECUSAR SOLICITAÇÃO RECEBIDA
# =====================================
class RejectFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nickname):
        sender = get_object_or_404(CustomUser, nickname=nickname)

        friendship = Friendship.objects.filter(
            sender=sender,
            receiver=request.user,
            status="pending"
        ).first()

        if not friendship:
            return Response(
                {"detail": "Nenhuma solicitação pendente deste usuário foi encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        friendship.delete()

        return Response(
            {"message": "Solicitação de amizade recusada com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# REMOVER AMIZADE
# =====================================
class RemoveFriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nickname):
        other_user = get_object_or_404(CustomUser, nickname=nickname)

        friendship = Friendship.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user),
            status="accepted"
        ).first()

        if not friendship:
            return Response(
                {"detail": "Este usuário não está na sua lista de amigos."},
                status=status.HTTP_404_NOT_FOUND
            )

        friendship.delete()

        return Response(
            {"message": "Amizade removida com sucesso."},
            status=status.HTTP_200_OK
        )

