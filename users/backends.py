from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


# =====================================
# AUTENTICAÇÃO COM EMAIL OU NICKNAME
# =====================================
# Este backend permite login usando:
# - email institucional
# - ou nickname
#
# Ele foi ajustado para aceitar tanto:
# - identifier (usado na API/JWT)
# - quanto username (compatibilidade com partes antigas)
class EmailOrNicknameBackend(ModelBackend):

    def authenticate(self, request, username=None, identifier=None, password=None, **kwargs):
        # ---------------------------------
        # DESCOBRE QUAL CAMPO DE LOGIN VEIO
        # ---------------------------------
        # Prioridade:
        # 1. identifier (novo padrão da API)
        # 2. username (compatibilidade)
        # 3. kwargs["username"]
        # 4. kwargs["identifier"]
        login_value = identifier or username or kwargs.get("username") or kwargs.get("identifier")

        if login_value is None or password is None:
            return None

        # remove espaços extras
        login_value = login_value.strip()

        try:
            # busca por email OU nickname
            user = User.objects.get(
                Q(email__iexact=login_value) | Q(nickname=login_value)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return None

        # valida senha e se o usuário pode autenticar
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None