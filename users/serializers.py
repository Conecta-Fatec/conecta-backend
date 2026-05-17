import re

from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import serializers

from email_verification.models import EmailVerification
from email_verification.services import read_registration_token

from .models import CustomUser, Friendship
from posts.models import Post, Community


def normalize_person_name(value):
    """Aceita letras e espaços, incluindo nomes compostos."""
    value = " ".join(value.strip().split())

    if not value:
        return value

    if not all(part.isalpha() for part in value.split(" ")):
        raise serializers.ValidationError("Use apenas letras e espaços.")

    return value

# =====================================
# SERIALIZER RESUMIDO DE COMUNIDADE
# =====================================
# Usado dentro do perfil para mostrar comunidades
# sem carregar dados excessivos.
class ProfileCommunitySerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "photo_url",
            "members_count",
        ]

    def get_members_count(self, obj):
        return obj.total_members()


    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None


# =====================================
# SERIALIZER RESUMIDO DE POST
# =====================================
# Usado dentro do perfil para listar os posts do usuário.
class ProfilePostSerializer(serializers.ModelSerializer):
    community_name = serializers.SerializerMethodField()
    community_slug = serializers.SerializerMethodField()
    edited = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "community_name",
            "community_slug",
            "edited",
            "created_at",
            "updated_at",
        ]

    def get_community_name(self, obj):
        if obj.community:
            return obj.community.name
        return None

    def get_community_slug(self, obj):
        if obj.community:
            return obj.community.slug
        return None

    def get_edited(self, obj):
        return obj.updated_at.replace(microsecond=0) > obj.created_at.replace(microsecond=0)


# =====================================
# SERIALIZER BASE DE USUÁRIO
# =====================================
# Esse serializer é usado no perfil privado.
# Agora ele já traz:
# - amigos
# - comunidades criadas
# - comunidades em que participa
# - posts do usuário
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    nickname_editable = serializers.SerializerMethodField()
    nickname_change_status = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    friends_count = serializers.SerializerMethodField()
    friends = serializers.SerializerMethodField()
    created_communities = serializers.SerializerMethodField()
    joined_communities = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "nickname",
            "email",
            "course",
            "bio",
            "photo",
            "photo_url",
            "nickname_editable",
            "nickname_change_status",
            "friends_count",
            "friends",
            "created_communities",
            "joined_communities",
            "posts",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_nickname_editable(self, obj):
        return obj.can_change_nickname()

    def get_nickname_change_status(self, obj):
        status = obj.get_nickname_change_status()
        next_reset_at = status.get("next_reset_at")

        return {
            "limit": status["limit"],
            "used": status["used"],
            "remaining": status["remaining"],
            "can_change": status["can_change"],
            "next_reset_at": next_reset_at.isoformat() if next_reset_at else None,
        }

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None

    def get_friends_count(self, obj):
        return obj.friends_count()

    def get_friends(self, obj):
        friends = obj.get_friends()

        return [
            {
                "id": friend.id,
                "full_name": f"{friend.first_name} {friend.last_name}".strip(),
                "nickname": friend.nickname,
                "photo_url": (
                    self.context["request"].build_absolute_uri(friend.photo.url)
                    if friend.photo and self.context.get("request")
                    else (friend.photo.url if friend.photo else None)
                ),
            }
            for friend in friends
        ]

    def get_created_communities(self, obj):
        communities = obj.created_communities.all().order_by("name")
        return ProfileCommunitySerializer(
            communities,
            many=True,
            context=self.context
        ).data

    def get_joined_communities(self, obj):
        communities = obj.communities.exclude(creator=obj).order_by("name")
        return ProfileCommunitySerializer(
            communities,
            many=True,
            context=self.context
        ).data

    def get_posts(self, obj):
        posts = obj.posts.all().select_related("community").order_by("-created_at")
        return ProfilePostSerializer(posts, many=True).data


# =====================================
# SERIALIZER DE PERFIL PÚBLICO
# =====================================
# Esse serializer mostra os dados públicos do usuário
# e também o status de amizade em relação ao usuário logado.
class PublicUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    friends_count = serializers.SerializerMethodField()
    created_communities = serializers.SerializerMethodField()
    joined_communities = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "nickname",
            "course",
            "bio",
            "photo",
            "photo_url",
            "friends_count",
            "created_communities",
            "joined_communities",
            "posts",
            "friendship_status",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None

    def get_friends_count(self, obj):
        return obj.friends_count()

    def get_created_communities(self, obj):
        communities = obj.created_communities.all().order_by("name")
        return ProfileCommunitySerializer(
            communities,
            many=True,
            context=self.context
        ).data

    def get_joined_communities(self, obj):
        communities = obj.communities.exclude(creator=obj).order_by("name")
        return ProfileCommunitySerializer(
            communities,
            many=True,
            context=self.context
        ).data

    def get_posts(self, obj):
        posts = obj.posts.all().select_related("community").order_by("-created_at")
        return ProfilePostSerializer(posts, many=True).data

    def get_friendship_status(self, obj):
        request = self.context.get("request")
        current_user = getattr(request, "user", None)

        if not current_user or not current_user.is_authenticated:
            return "anonymous"

        if current_user == obj:
            return "self"

        if current_user.is_friends_with(obj):
            return "friends"

        if current_user.sent_friend_request_to(obj):
            return "request_sent"

        if current_user.received_friend_request_from(obj):
            return "request_received"

        return "not_friends"


# =====================================
# SERIALIZER DE AMIZADE
# =====================================
# Exibe uma solicitação/amizade com os dois lados.
class FriendshipSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = [
            "id",
            "sender",
            "receiver",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_user_data(self, user):
        request = self.context.get("request")

        photo_url = None
        if user.photo:
            photo_url = (
                request.build_absolute_uri(user.photo.url)
                if request
                else user.photo.url
            )

        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "nickname": user.nickname,
            "course": user.course,
            "bio": user.bio,
            "photo_url": photo_url,
            "friends_count": user.friends_count(),
        }

    def get_sender(self, obj):
        return self.get_user_data(obj.sender)

    def get_receiver(self, obj):
        return self.get_user_data(obj.receiver)


# =====================================
# SERIALIZER RESUMIDO DE USUÁRIO
# =====================================
# Usado em busca de usuários e listas de amigos públicas.
class UserCardSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    friends_count = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "nickname",
            "course",
            "bio",
            "photo_url",
            "friends_count",
            "friendship_status",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None

    def get_friends_count(self, obj):
        return obj.friends_count()

    def get_friendship_status(self, obj):
        request = self.context.get("request")
        current_user = getattr(request, "user", None)

        if not current_user or not current_user.is_authenticated:
            return "anonymous"

        if current_user == obj:
            return "self"

        if current_user.is_friends_with(obj):
            return "friends"

        if current_user.sent_friend_request_to(obj):
            return "request_sent"

        if current_user.received_friend_request_from(obj):
            return "request_received"

        return "not_friends"


# =====================================
# SERIALIZER DE CADASTRO
# =====================================
# O cadastro não recebe mais email direto do frontend.
# O email é extraído do registration_token, gerado após a confirmação do código.
class RegisterSerializer(serializers.ModelSerializer):
    registration_token = serializers.CharField(
        write_only=True,
        error_messages={
            "blank": "O token de verificação é obrigatório.",
            "required": "O token de verificação é obrigatório.",
        }
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "A senha deve ter no mínimo 8 caracteres.",
            "blank": "A senha é obrigatória.",
            "required": "A senha é obrigatória.",
        }
    )

    confirm_password = serializers.CharField(
        write_only=True,
        error_messages={
            "blank": "A confirmação de senha é obrigatória.",
            "required": "A confirmação de senha é obrigatória.",
        }
    )

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "nickname",
            "registration_token",
            "password",
            "confirm_password",
        ]

    def validate_first_name(self, value):
        value = normalize_person_name(value)

        if not value:
            raise serializers.ValidationError("O nome é obrigatório.")

        return value

    def validate_last_name(self, value):
        value = normalize_person_name(value)

        if not value:
            raise serializers.ValidationError("O sobrenome é obrigatório.")

        return value

    def validate_nickname(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("O nickname é obrigatório.")

        if not re.fullmatch(r"[a-z0-9]+", value):
            raise serializers.ValidationError(
                "O nickname deve conter apenas letras minúsculas e números."
            )

        if CustomUser.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("Este nickname já está em uso.")

        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        registration_token = attrs.get("registration_token")

        if password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "As senhas não coincidem."
            })

        # Lê o token temporário criado após o usuário acertar o código.
        # Se o token foi alterado, expirou ou não existe, o cadastro é bloqueado.
        try:
            token_data = read_registration_token(registration_token)
        except SignatureExpired:
            raise serializers.ValidationError({
                "registration_token": "Token de cadastro expirado. Solicite um novo código."
            })
        except BadSignature:
            raise serializers.ValidationError({
                "registration_token": "Token de cadastro inválido. Confirme o email novamente."
            })

        verification_id = token_data.get("verification_id")
        email = str(token_data.get("email", "")).strip().lower()
        purpose = token_data.get("purpose")

        if purpose != EmailVerification.PURPOSE_REGISTER:
            raise serializers.ValidationError({
                "registration_token": "Token de cadastro inválido."
            })

        try:
            verification = EmailVerification.objects.get(
                id=verification_id,
                email__iexact=email,
                purpose=EmailVerification.PURPOSE_REGISTER,
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError({
                "registration_token": "Verificação de email não encontrada."
            })

        if not verification.is_confirmed:
            raise serializers.ValidationError({
                "registration_token": "Confirme o código enviado para o email antes de cadastrar."
            })

        if verification.is_registered:
            raise serializers.ValidationError({
                "registration_token": "Este token de cadastro já foi utilizado."
            })

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({
                "registration_token": "Email já cadastrado no nosso site."
            })

        # O email final vem somente da verificação confirmada.
        # Assim o usuário não consegue trocar o email manualmente no cadastro.
        attrs["email"] = email
        attrs["verification"] = verification
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        validated_data.pop("registration_token")
        verification = validated_data.pop("verification")

        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            nickname=validated_data["nickname"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        # Marca a verificação como usada para impedir reutilização do mesmo token.
        verification.registered_at = timezone.now()
        verification.save(update_fields=["registered_at", "updated_at"])

        return user


# =====================================
# SERIALIZER DE ATUALIZAÇÃO DE PERFIL
# =====================================
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "nickname",
            "photo",
            "course",
            "bio",
        ]

    def validate_first_name(self, value):
        value = normalize_person_name(value)

        if not value:
            raise serializers.ValidationError("O nome é obrigatório.")

        return value

    def validate_last_name(self, value):
        value = normalize_person_name(value)

        if not value:
            raise serializers.ValidationError("O sobrenome é obrigatório.")

        return value

    def validate_nickname(self, value):
        value = value.strip()
        user = self.instance

        if not value:
            raise serializers.ValidationError("O nickname é obrigatório.")

        if not re.fullmatch(r"[a-z0-9]+", value):
            raise serializers.ValidationError(
                "O nickname deve conter apenas letras minúsculas e números."
            )

        if value != user.nickname:
            change_status = user.get_nickname_change_status()

            if not change_status["can_change"]:
                next_reset_at = change_status.get("next_reset_at")
                reset_message = (
                    f" Você poderá alterar novamente em {next_reset_at.strftime('%d/%m/%Y')}."
                    if next_reset_at
                    else ""
                )
                raise serializers.ValidationError(
                    "Você pode alterar o nickname no máximo 2 vezes a cada 20 dias."
                    + reset_message
                )

        if CustomUser.objects.filter(nickname=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Este nickname já está em uso.")

        return value

    def validate_bio(self, value):
        # Mantém a bio em uma linha, sem quebras escondidas.
        value = " ".join(value.strip().split())

        if len(value) > 150:
            raise serializers.ValidationError(
                "A biografia deve ter no máximo 150 caracteres."
            )

        return value

    def update(self, instance, validated_data):
        old_nickname = instance.nickname
        new_nickname = validated_data.get("nickname", old_nickname)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if old_nickname != new_nickname:
            instance.register_nickname_change()

        instance.save()
        return instance


# =====================================
# SERIALIZER DE LOGIN SIMPLES
# =====================================
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        error_messages={
            "blank": "Email ou nickname é obrigatório.",
            "required": "Email ou nickname é obrigatório.",
        }
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={
            "blank": "A senha é obrigatória.",
            "required": "A senha é obrigatória.",
        }
    )

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = authenticate(
            identifier=identifier,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                {"detail": "Credenciais inválidas. Verifique email/nickname e senha."}
            )

        attrs["user"] = user
        return attrs
