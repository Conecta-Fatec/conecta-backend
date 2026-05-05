from rest_framework_simplejwt.views import TokenObtainPairView

from .jwt_serializers import CustomTokenObtainPairSerializer


# =====================================
# VIEW DE LOGIN JWT PERSONALIZADA
# =====================================
# Esta view usa o serializer customizado que:
# - aceita email ou nickname
# - valida a senha
# - gera access token e refresh token
# - devolve também os dados básicos do usuário
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer