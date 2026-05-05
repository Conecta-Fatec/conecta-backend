from django.contrib import admin
from django.contrib.auth import get_user_model

# Pegando o seu modelo de usuário customizado
User = get_user_model()

# Dando a ordem para o Django mostrar ele no painel
admin.site.register(User)