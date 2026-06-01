from rest_framework import serializers

from .models import Community, Post, Comment


# =====================================
# SERIALIZER RESUMIDO DO AUTOR
# =====================================
# Usado dentro de comunidades, posts e comentários
# para o frontend receber os dados essenciais do usuário.
class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    course = serializers.CharField(read_only=True)
    bio = serializers.CharField(read_only=True)
    friends_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    def get_friends_count(self, obj):
        return obj.friends_count()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None


# =====================================
# SERIALIZER DE COMUNIDADE
# =====================================
# Exibe os dados principais da comunidade e também
# algumas informações derivadas úteis para o frontend.
class CommunitySerializer(serializers.ModelSerializer):
    creator = AuthorSerializer(read_only=True)
    total_members = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            "id",
            "creator",
            "name",
            "slug",
            "description",
            "photo",
            "photo_url",
            "total_members",
            "is_member",
            "is_creator",
            "created_at",
            "updated_at",
        ]

    def get_total_members(self, obj):
        return obj.total_members()

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None

    def get_is_member(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            return obj.members.filter(id=user.id).exists()

        return False

    def get_is_creator(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            return obj.creator_id == user.id

        return False


# =====================================
# SERIALIZER DE CRIAÇÃO/EDIÇÃO DE COMUNIDADE
# =====================================
# Regras mantidas:
# - nome obrigatório
# - descrição com no máximo 150 caracteres
# - usuário pode criar no máximo 3 comunidades
class CommunityWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = [
            "name",
            "description",
            "photo",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("O nome da comunidade é obrigatório.")

        return value

    def validate_description(self, value):
        value = value.strip()

        if len(value) > 150:
            raise serializers.ValidationError(
                "A descrição da comunidade deve ter no máximo 150 caracteres."
            )

        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        # Só valida limite de criação quando for uma criação nova
        if self.instance is None and user:
            if Community.objects.filter(creator=user).count() >= 3:
                raise serializers.ValidationError({
                    "detail": "Você pode criar no máximo 3 comunidades."
                })

        return attrs


# =====================================
# SERIALIZER RESUMIDO DE COMUNIDADE
# =====================================
# Usado dentro do post para evitar payload muito grande.
# Usado dentro do post para evitar payload muito grande.
class CommunityMiniSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Community
        fields = [
            "id",
            "name",
            "slug",
            "photo_url",
            "members_count"
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None

    def get_members_count(self, obj):
        return obj.total_members()

# =====================================
# SERIALIZER DE COMENTÁRIO
# =====================================
# Exibe:
# - autor
# - comentário pai (se houver)
# - likes
# - se foi editado
# - se o usuário atual curtiu

class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    total_likes = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField() 

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "post",
            "parent",
            "content",
            "edited",
            "total_likes",
            "liked_by_me",
            "replies_count",
            "replies",
            "gif_url",
            "created_at",
            "updated_at",
        ]

    def get_total_likes(self, obj):
        # Conta as curtidas na memória usando len() em vez de viagem ao banco
        return len(obj.likes.all())

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            # Mantém a verificação na memória
            return user in obj.likes.all()

        return False

    def get_replies_count(self, obj):
        # Lê a lista da memória que o PostSerializer vai nos dar!
        all_comments = self.context.get("all_post_comments", [])
        if not all_comments: # Segurança caso seja acessado de outro lugar
            all_comments = list(obj.post.comments.all())
            
        replies = [c for c in all_comments if c.parent_id == obj.id]
        return len(replies)

    def get_replies(self, obj):
        # Lê a lista da memória
        all_comments = self.context.get("all_post_comments", [])
        if not all_comments:
            all_comments = list(obj.post.comments.all())
            
        replies = [c for c in all_comments if c.parent_id == obj.id]
        replies.sort(key=lambda x: x.created_at)
        
        # Repassa o mesmo contexto para as respostas
        serializer = CommentSerializer(replies, many=True, context=self.context)
        return serializer.data

# =====================================
# SERIALIZER DE CRIAÇÃO/EDIÇÃO DE COMENTÁRIO
# =====================================
# Mantém a regra de no máximo 200 caracteres.
class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "content",
        ]

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("O comentário não pode ficar vazio.")

        if len(value) > 200:
            raise serializers.ValidationError(
                "O comentário deve ter no máximo 200 caracteres."
            )

        return value


# =====================================
# SERIALIZER DE POST
# =====================================
# Exibe:
# - autor
# - comunidade (quando existir)
# - likes
# - se o usuário atual curtiu
# - comentários principais
class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    community = CommunityMiniSerializer(read_only=True)
    total_likes = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    top_level_comments = serializers.SerializerMethodField()
    edited = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "community",
            "content",
            "edited",
            "total_likes",
            "liked_by_me",
            "comments_count",
            "top_level_comments",
            "created_at",
            "gif_url",
            "updated_at",
        ]

    def get_total_likes(self, obj):
        # Usamos len() com .all() para contar direto na memória 
        # e não fazer o banco de dados trabalhar de novo.
        return len(obj.likes.all())

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            return user in obj.likes.all()

        return False

    def get_comments_count(self, obj):
        # Trocamos o .count() pelo len() para manter na memória!
        return len(obj.comments.all())

    def get_top_level_comments(self, obj):
        all_comments = list(obj.comments.all())
        comments = [c for c in all_comments if c.parent_id is None]
        comments.sort(key=lambda x: x.created_at)
        
        context = self.context.copy()
        context["all_post_comments"] = all_comments
        
        serializer = CommentSerializer(
            comments,
            many=True,
            context=context
        )
        return serializer.data

    def get_edited(self, obj):
        # Considera editado apenas se houve diferença perceptível
        # após a criação do post.
        return obj.updated_at.replace(microsecond=0) > obj.created_at.replace(microsecond=0)

# =====================================
# SERIALIZER DE CRIAÇÃO/EDIÇÃO DE POST
# =====================================
# Mantém a regra de no máximo 200 caracteres.
class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            "content",
            "community",
        ]

    def validate_content(self, value):
        # Remove quebras de linha/espaços duplicados.
        # A ação de postar com Enter fica no frontend.
        value = " ".join(value.strip().split())

        if not value:
            raise serializers.ValidationError("O post não pode ficar vazio.")

        if len(value) > 200:
            raise serializers.ValidationError(
                "O post deve ter no máximo 200 caracteres."
            )

        return value

    def validate_community(self, value):
        request = self.context.get("request")
        user = request.user if request else None

        # community pode ser nulo, porque existe post do feed normal
        if value and user:
            if not value.members.filter(id=user.id).exists():
                raise serializers.ValidationError(
                    "Você precisa participar da comunidade para postar nela."
                )

        return value