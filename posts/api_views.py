from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Community, Post, Comment
from .serializers import (
    AuthorSerializer,
    CommunitySerializer,
    CommunityWriteSerializer,
    PostSerializer,
    PostWriteSerializer,
    CommentSerializer,
    CommentWriteSerializer,
)# =====================================
# FEED GLOBAL
# =====================================



class FeedAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        posts = Post.objects.filter(community__isnull=True).select_related(
            "author"
        ).prefetch_related(
            "likes", 
            "comments", 
            "comments__author",
            "author__sent_friendships__receiver",
            "author__received_friendships__sender"
        ).order_by("-created_at")

        serializer = PostSerializer(
            posts,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================
# CRIAR POST NO FEED
# =====================================
# Cria um post normal, sem comunidade.
class CreateFeedPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostWriteSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            post = serializer.save(
                author=request.user,
                community=None
            )

            response_serializer = PostSerializer(
                post,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Post criado com sucesso.",
                    "post": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# EDITAR POST
# =====================================
# Só o autor pode editar.
class UpdatePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, author=request.user)

        serializer = PostWriteSerializer(
            post,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_post = serializer.save()

            response_serializer = PostSerializer(
                updated_post,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Post atualizado com sucesso.",
                    "post": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, author=request.user)

        serializer = PostWriteSerializer(
            post,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_post = serializer.save()

            response_serializer = PostSerializer(
                updated_post,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Post atualizado com sucesso.",
                    "post": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# EXCLUIR POST
# =====================================
# Só o autor pode excluir.
class DeletePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, author=request.user)
        post.delete()

        return Response(
            {"message": "Post excluído com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# CURTIR / DESCURTIR POST
# =====================================
class ToggleLikePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
            message = "Curtida removida com sucesso."
        else:
            post.likes.add(request.user)
            liked = True
            message = "Post curtido com sucesso."

        return Response(
            {
                "message": message,
                "liked": liked,
                "total_likes": post.total_likes(),
            },
            status=status.HTTP_200_OK
        )


# =====================================
# LISTAR COMUNIDADES
# =====================================
# Retorna:
# - comunidades do usuário
# - outras comunidades
# - quantidade criadas pelo usuário
class CommunityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        my_communities = user.communities.all().order_by("name")
        other_communities = Community.objects.exclude(members=user).order_by("name")
        created_communities_count = Community.objects.filter(creator=user).count()

        return Response(
            {
                "my_communities": CommunitySerializer(
                    my_communities,
                    many=True,
                    context={"request": request}
                ).data,
                "other_communities": CommunitySerializer(
                    other_communities,
                    many=True,
                    context={"request": request}
                ).data,
                "created_communities_count": created_communities_count,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# CRIAR COMUNIDADE
# =====================================
# Regras:
# - nome obrigatório
# - descrição até 150 caracteres
# - usuário pode criar no máximo 3
# - criador entra automaticamente como membro
class CreateCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CommunityWriteSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            community = serializer.save(creator=request.user)

            # Criador entra automaticamente como membro
            community.members.add(request.user)

            response_serializer = CommunitySerializer(
                community,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comunidade criada com sucesso.",
                    "community": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# DETALHE DA COMUNIDADE
# =====================================
# Retorna:
# - dados da comunidade
# - posts da comunidade
# - membros
# - quantidade de membros
# - se o usuário logado participa
class CommunityDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        community = get_object_or_404(Community, slug=slug)

        posts = community.posts.select_related(
            "author"
        ).prefetch_related(
            "likes", 
            "comments", 
            "comments__author"
        ).order_by("-created_at")
        members = community.members.all().order_by("first_name", "last_name")

        is_member = False
        if request.user.is_authenticated:
            is_member = community.members.filter(id=request.user.id).exists()

        return Response(
            {
                "community": CommunitySerializer(
                    community,
                    context={"request": request}
                ).data,
                "posts": PostSerializer(
                    posts,
                    many=True,
                    context={"request": request}
                ).data,
                "members": AuthorSerializer(
                    members,
                    many=True,
                    context={"request": request}
                ).data,
                "members_count": community.total_members(),
                "is_member": is_member,
            },
            status=status.HTTP_200_OK
        )


# =====================================
# CRIAR POST NA COMUNIDADE
# =====================================
# Só pode postar se for membro da comunidade.
class CreateCommunityPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)

        if not community.members.filter(id=request.user.id).exists():
            return Response(
                {"detail": "Você precisa participar da comunidade para postar nela."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PostWriteSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            post = serializer.save(
                author=request.user,
                community=community
            )

            response_serializer = PostSerializer(
                post,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Post criado com sucesso na comunidade.",
                    "post": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# ENTRAR NA COMUNIDADE
# =====================================
class JoinCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        community.members.add(request.user)

        return Response(
            {"message": "Você entrou na comunidade com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# SAIR DA COMUNIDADE
# =====================================
class LeaveCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        community.members.remove(request.user)

        return Response(
            {"message": "Você saiu da comunidade com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# EDITAR COMUNIDADE
# =====================================
# Só o criador pode editar.
class UpdateCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, slug):
        community = get_object_or_404(Community, slug=slug, creator=request.user)

        serializer = CommunityWriteSerializer(
            community,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            old_name = community.name
            updated_community = serializer.save()

            # Se o nome mudou, regeneramos o slug
            if old_name != updated_community.name:
                updated_community.slug = ""
                updated_community.save()

            response_serializer = CommunitySerializer(
                updated_community,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comunidade atualizada com sucesso.",
                    "community": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, slug):
        community = get_object_or_404(Community, slug=slug, creator=request.user)

        serializer = CommunityWriteSerializer(
            community,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            old_name = community.name
            updated_community = serializer.save()

            if old_name != updated_community.name:
                updated_community.slug = ""
                updated_community.save()

            response_serializer = CommunitySerializer(
                updated_community,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comunidade atualizada com sucesso.",
                    "community": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# EXCLUIR COMUNIDADE
# =====================================
# Só o criador pode excluir.
class DeleteCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug):
        community = get_object_or_404(Community, slug=slug, creator=request.user)
        community.delete()

        return Response(
            {"message": "Comunidade excluída com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# CRIAR COMENTÁRIO EM POST
# =====================================
class CreateCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        serializer = CommentWriteSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(
                author=request.user,
                post=post
            )

            response_serializer = CommentSerializer(
                comment,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comentário criado com sucesso.",
                    "comment": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# RESPONDER COMENTÁRIO
# =====================================
class ReplyCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        parent_comment = get_object_or_404(Comment, id=comment_id)

        serializer = CommentWriteSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(
                author=request.user,
                post=parent_comment.post,
                parent=parent_comment
            )

            response_serializer = CommentSerializer(
                comment,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Resposta criada com sucesso.",
                    "comment": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# EDITAR COMENTÁRIO
# =====================================
# Só o autor pode editar.
class UpdateCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, author=request.user)

        serializer = CommentWriteSerializer(comment, data=request.data)

        if serializer.is_valid():
            updated_comment = serializer.save()
            updated_comment.edited = True
            updated_comment.save()

            response_serializer = CommentSerializer(
                updated_comment,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comentário atualizado com sucesso.",
                    "comment": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, author=request.user)

        serializer = CommentWriteSerializer(
            comment,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            updated_comment = serializer.save()
            updated_comment.edited = True
            updated_comment.save()

            response_serializer = CommentSerializer(
                updated_comment,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Comentário atualizado com sucesso.",
                    "comment": response_serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# EXCLUIR COMENTÁRIO
# =====================================
# Só o autor pode excluir.
class DeleteCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, author=request.user)
        comment.delete()

        return Response(
            {"message": "Comentário excluído com sucesso."},
            status=status.HTTP_200_OK
        )


# =====================================
# CURTIR / DESCURTIR COMENTÁRIO
# =====================================
class ToggleLikeCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.likes.filter(id=request.user.id).exists():
            comment.likes.remove(request.user)
            liked = False
            message = "Curtida removida com sucesso."
        else:
            comment.likes.add(request.user)
            liked = True
            message = "Comentário curtido com sucesso."

        return Response(
            {
                "message": message,
                "liked": liked,
                "total_likes": comment.total_likes(),
            },
            status=status.HTTP_200_OK
        )
