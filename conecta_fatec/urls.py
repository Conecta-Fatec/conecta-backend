from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from users.jwt_views import CustomTokenObtainPairView
from django.http import HttpResponse


#Função para rodar 24hrs
def health_check(request):
    return HttpResponse("Servidor Online", status=200)
# =====================================
# ROTAS PRINCIPAIS DO PROJETO
# =====================================
# Aqui concentramos:
# - painel admin
# - rotas da API de usuários
# - rotas da API de posts
# - autenticação JWT
# - suporte ao login visual do DRF para testes
urlpatterns = [
    #Função para rodar 24hrs
    path('', health_check),

    # Painel administrativo
    path("admin/", admin.site.urls),

    # API de usuários
    path("api/users/", include(("users.urls", "users"), namespace="users")),

    # API de posts
    path("api/posts/", include(("posts.urls", "posts"), namespace="posts")),

    # Login visual do DRF (útil em testes no navegador)
    path("api-auth/", include("rest_framework.urls")),

    # JWT - obter token
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),

    # JWT - renovar token
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]


# =====================================
# ARQUIVOS DE MÍDIA EM DESENVOLVIMENTO
# =====================================
# Permite acessar fotos enviadas pelo projeto enquanto DEBUG=True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)