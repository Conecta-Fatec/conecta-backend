from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# =====================================
# SERIALIZER JWT PERSONALIZADO
# =====================================
# Aqui trocamos o campo padrão de login do SimpleJWT
# para "identifier", assim o formulário do DRF e o frontend
# passam a usar apenas:
# - identifier
# - password
#
# O identifier poderá receber:
# - email
# - ou nickname
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Substitui o campo padrão herdado (que no seu caso era "email")
    username_field = "identifier"

    password = serializers.CharField(
        write_only=True,
        error_messages={
            "blank": "A senha é obrigatória.",
            "required": "A senha é obrigatória.",
        }
    )

    # ---------------------------------
    # VALIDAÇÃO DO LOGIN
    # ---------------------------------
    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        # Usa seu backend customizado:
        # login por email OU nickname
        user = authenticate(
            request=self.context.get("request"),
            identifier=identifier,
            password=password,
        )

        if not user:
            raise serializers.ValidationError({
                "detail": "Credenciais inválidas. Verifique email/nickname e senha."
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "Este usuário está inativo."
            })

        # Gera os tokens JWT
        refresh = self.get_token(user)
        access = refresh.access_token

        # Retorna token + dados básicos do usuário
        return {
            "refresh": str(refresh),
            "access": str(access),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "nickname": user.nickname,
                "email": user.email,
                "course": user.course,
                "bio": user.bio,
                "nickname_editable": user.can_change_nickname(),
                "photo_url": (
                    self.context["request"].build_absolute_uri(user.photo.url)
                    if user.photo and self.context.get("request")
                    else (user.photo.url if user.photo else None)
                ),
            }
        }

    # ---------------------------------
    # TOKEN PERSONALIZADO
    # ---------------------------------
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["user_id"] = user.id
        token["nickname"] = user.nickname
        token["email"] = user.email

        return token