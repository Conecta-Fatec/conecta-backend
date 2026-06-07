from django.shortcuts import get_object_or_404
from django.db.models import Count, Prefetch

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
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
)


# ==========================================
# PAGINACAO
# ==========================================

class PaginacaoPadrao(PageNumberPagination):
    """
    Paginacao usada em todos os endpoints que retornam listas.

    Parametros de URL:
      ?page=2          — pagina desejada
      ?page_size=5     — itens por pagina (maximo: 50)

    Manutencao: ajuste PAGE_SIZE e MAX_PAGE_SIZE conforme necessidade.
    """
    page_size            = 10
    page_size_query_param = 'page_size'
    max_page_size        = 50


# ==========================================
# QUERYSETS REUTILIZAVEIS
# ==========================================
# Centraliza as queries mais pesadas para evitar repeticao entre views
# e garantir que o prefetch/annotate seja consistente em todos os endpoints.

def _queryset_posts_completo():
    """
    Retorna um queryset de Post com todos os relacionamentos pre-carregados
    e total_likes calculado via anotacao (sem query extra por post).

    Usado pelo feed global e pelo detalhe de comunidade.
    """
    return (
        Post.objects
        .select_related("author")
        .prefetch_related(
            # Likes do post (ManyToMany — prefetch e mais eficiente que select_related)
            "likes",
            # Comentarios com todos os sub-relacionamentos necessarios
            Prefetch(
                "comments",
                queryset=Comment.objects
                    .select_related("author")
                    .prefetch_related(
                        "likes",
                        "author__sent_friendships__receiver",
                        "author__received_friendships__sender",
                    )
                    .annotate(likes_count=Count("likes", distinct=True))
                    .order_by("created_at")
            ),
            # Amizades do autor do post
            "author__sent_friendships__receiver",
            "author__received_friendships__sender",
        )
        # likes_count substitui a chamada a post.total_likes() — nenhuma query extra
        .annotate(likes_count=Count("likes", distinct=True))
    )


def _queryset_comunidades_completo():
    """
    Retorna um queryset de Community com total_members anotado.
    Elimina a chamada a community.total_members() como query separada.
    """
    return Community.objects.annotate(
        members_count_annotation=Count("members", distinct=True)
    )


# ==========================================
# FEED GLOBAL
# ==========================================

class FeedAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        posts = (
            _queryset_posts_completo()
            .filter(community__isnull=True)
            .order_by("-created_at")
        )

        paginador = PaginacaoPadrao()
        pagina = paginador.paginate_queryset(posts, request)

        serializer = PostSerializer(
            pagina,
            many=True,
            context={"request": request}
        )

        return paginador.get_paginated_response(serializer.data)


# ==========================================
# CRIAR POST NO FEED
# ==========================================

class CreateFeedPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostWriteSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            post = serializer.save(author=request.user, community=None)

            return Response(
                {
                    "message": "Post criado com sucesso.",
                    "post": PostSerializer(post, context={"request": request}).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# EDITAR POST
# ==========================================
# Só o autor pode editar.

class UpdatePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _atualizar(self, request, post_id, partial=False):
        post = get_object_or_404(Post, id=post_id, author=request.user)

        serializer = PostWriteSerializer(
            post,
            data=request.data,
            partial=partial,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_post = serializer.save()
            return Response(
                {
                    "message": "Post atualizado com sucesso.",
                    "post": PostSerializer(updated_post, context={"request": request}).data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, post_id):
        return self._atualizar(request, post_id, partial=False)

    def patch(self, request, post_id):
        return self._atualizar(request, post_id, partial=True)


# ==========================================
# EXCLUIR POST
# ==========================================
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


# ==========================================
# CURTIR / DESCURTIR POST
# ==========================================

class ToggleLikePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # Anota o total_likes direto na query para nao fazer segunda query no retorno
        post = get_object_or_404(
            Post.objects.annotate(likes_count=Count("likes", distinct=True)),
            id=post_id
        )

        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked   = False
            message = "Curtida removida com sucesso."
            total   = post.likes_count - 1
        else:
            post.likes.add(request.user)
            liked   = True
            message = "Post curtido com sucesso."
            total   = post.likes_count + 1

        return Response(
            {
                "message": message,
                "liked":       liked,
                "total_likes": total,
            },
            status=status.HTTP_200_OK
        )


# ==========================================
# LISTAR COMUNIDADES
# ==========================================
# Retorna comunidades do usuario, outras comunidades (paginadas)
# e quantidade criadas pelo usuario — tudo em queries otimizadas.

class CommunityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Comunidades do usuario: sem limite (tendem a ser poucas)
        my_communities = (
            _queryset_comunidades_completo()
            .filter(members=user)
            .order_by("name")
        )

        # Outras comunidades: paginadas para nao carregar tudo de uma vez
        other_communities_qs = (
            _queryset_comunidades_completo()
            .exclude(members=user)
            .order_by("name")
        )

        # Contagem de criadas pelo usuario: query simples de agregacao
        created_count = Community.objects.filter(creator=user).count()

        paginador = PaginacaoPadrao()
        other_paginated = paginador.paginate_queryset(other_communities_qs, request)

        return Response(
            {
                "my_communities": CommunitySerializer(
                    my_communities,
                    many=True,
                    context={"request": request}
                ).data,
                "other_communities": CommunitySerializer(
                    other_paginated,
                    many=True,
                    context={"request": request}
                ).data,
                "other_communities_total": paginador.page.paginator.count,
                "other_communities_next":  paginador.get_next_link(),
                "created_communities_count": created_count,
            },
            status=status.HTTP_200_OK
        )


# ==========================================
# CRIAR COMUNIDADE
# ==========================================
# Regras:
# - nome obrigatorio
# - descricao ate 150 caracteres
# - usuario pode criar no maximo 3
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
            community.members.add(request.user)

            return Response(
                {
                    "message": "Comunidade criada com sucesso.",
                    "community": CommunitySerializer(
                        community, context={"request": request}
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

# Adicione este import lá no topo do seu arquivo views.py (se já não tiver):
from rest_framework.pagination import PageNumberPagination

# =====================================
# DETALHE DA COMUNIDADE (Com Paginação)
# =====================================
class CommunityDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        # 1. Busca a comunidade normalmente
        community = get_object_or_404(Community, slug=slug)

        # 2. Busca os posts com a NOSSA otimização completa (sem limite fixo)
        posts = Post.objects.filter(community=community).select_related(
            "author"
        ).prefetch_related(
            "likes", 
            "comments", 
            "comments__author",
            "comments__likes",
            "author__sent_friendships__receiver",
            "author__received_friendships__sender"
        ).order_by("-created_at")

        # 3. Busca os membros com otimização (adaptado para o FATEC)
        members = community.members.prefetch_related(
            "sent_friendships__receiver",
            "received_friendships__sender"
        ).order_by("first_name", "last_name")

        is_member = False
        if request.user.is_authenticated:
            is_member = community.members.filter(id=request.user.id).exists()

        # 4. Configura a Paginação Nativa do Django REST
        paginador = PageNumberPagination()
        paginador.page_size = 30 # Quantidade de posts por página!
        posts_paginados = paginador.paginate_queryset(posts, request)

        return Response(
            {
                "community": CommunitySerializer(
                    community, context={"request": request}
                ).data,
                "posts": PostSerializer(
                    posts_paginados,
                    many=True,
                    context={"request": request}
                ).data,
                "posts_next": paginador.get_next_link(),
                "posts_total": paginador.page.paginator.count,
                "members": AuthorSerializer(
                    members,
                    many=True,
                    context={"request": request}
                ).data,
                # Mantive a sua função original que já funciona perfeitamente:
                "members_count": community.total_members(),
                "is_member": is_member,
            },
            status=status.HTTP_200_OK
        )

# ==========================================
# CRIAR POST NA COMUNIDADE
# ==========================================
# Só pode postar se for membro.

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
            post = serializer.save(author=request.user, community=community)

            return Response(
                {
                    "message": "Post criado com sucesso na comunidade.",
                    "post": PostSerializer(post, context={"request": request}).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# ENTRAR NA COMUNIDADE
# ==========================================

class JoinCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        community.members.add(request.user)

        return Response(
            {"message": "Você entrou na comunidade com sucesso."},
            status=status.HTTP_200_OK
        )


# ==========================================
# SAIR DA COMUNIDADE
# ==========================================

class LeaveCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        community.members.remove(request.user)

        return Response(
            {"message": "Você saiu da comunidade com sucesso."},
            status=status.HTTP_200_OK
        )


# ==========================================
# EDITAR COMUNIDADE
# ==========================================
# Só o criador pode editar.
# Corrigido: o slug agora e regenerado dentro do serializer/model.save()
# em uma unica operacao, sem double save.

class UpdateCommunityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _atualizar(self, request, slug, partial=False):
        community = get_object_or_404(Community, slug=slug, creator=request.user)
        nome_anterior = community.name

        serializer = CommunityWriteSerializer(
            community,
            data=request.data,
            partial=partial,
            context={"request": request}
        )

        if serializer.is_valid():
            # Se o nome mudou, limpa o slug ANTES do save para que o
            # modelo/signal regenere em uma unica operacao.
            if nome_anterior != serializer.validated_data.get("name", nome_anterior):
                serializer.validated_data["slug"] = ""

            updated_community = serializer.save()

            return Response(
                {
                    "message": "Comunidade atualizada com sucesso.",
                    "community": CommunitySerializer(
                        updated_community, context={"request": request}
                    ).data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug):
        return self._atualizar(request, slug, partial=False)

    def patch(self, request, slug):
        return self._atualizar(request, slug, partial=True)


# ==========================================
# EXCLUIR COMUNIDADE
# ==========================================
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


# ==========================================
# CRIAR COMENTÁRIO EM POST
# ==========================================

class CreateCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = CommentWriteSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(author=request.user, post=post)

            return Response(
                {
                    "message": "Comentário criado com sucesso.",
                    "comment": CommentSerializer(
                        comment, context={"request": request}
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# RESPONDER COMENTÁRIO
# ==========================================

class ReplyCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        parent = get_object_or_404(
            Comment.objects.select_related("post"),
            id=comment_id
        )
        serializer = CommentWriteSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(
                author=request.user,
                post=parent.post,
                parent=parent
            )

            return Response(
                {
                    "message": "Resposta criada com sucesso.",
                    "comment": CommentSerializer(
                        comment, context={"request": request}
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# EDITAR COMENTÁRIO
# ==========================================
# Só o autor pode editar.

class UpdateCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _atualizar(self, request, comment_id, partial=False):
        comment = get_object_or_404(Comment, id=comment_id, author=request.user)

        serializer = CommentWriteSerializer(
            comment,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            # Marca como editado e salva em uma unica operacao
            updated_comment = serializer.save(edited=True)

            return Response(
                {
                    "message": "Comentário atualizado com sucesso.",
                    "comment": CommentSerializer(
                        updated_comment, context={"request": request}
                    ).data
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, comment_id):
        return self._atualizar(request, comment_id, partial=False)

    def patch(self, request, comment_id):
        return self._atualizar(request, comment_id, partial=True)


# ==========================================
# EXCLUIR COMENTÁRIO
# ==========================================
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


# ==========================================
# CURTIR / DESCURTIR COMENTÁRIO
# ==========================================

class ToggleLikeCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(
            Comment.objects.annotate(likes_count=Count("likes", distinct=True)),
            id=comment_id
        )

        if comment.likes.filter(id=request.user.id).exists():
            comment.likes.remove(request.user)
            liked   = False
            message = "Curtida removida com sucesso."
            total   = comment.likes_count - 1
        else:
            comment.likes.add(request.user)
            liked   = True
            message = "Comentário curtido com sucesso."
            total   = comment.likes_count + 1

        return Response(
            {
                "message": message,
                "liked":       liked,
                "total_likes": total,
            },
            status=status.HTTP_200_OK
        )
    
# ==========================================
# DETALHE DO POST (VER POST COMPLETO)
# ==========================================
class PostDetailAPIView(APIView):
    permission_classes = [AllowAny] # Permite ver o post mesmo sem estar logado

    def get(self, request, post_id):
        # Usa a sua query super otimizada que já traz likes, comentários e amizades!
        post = get_object_or_404(
            _queryset_posts_completo(),
            id=post_id
        )

        serializer = PostSerializer(
            post,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)    
    