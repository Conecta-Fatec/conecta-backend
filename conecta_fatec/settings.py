from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
# =====================================
# CAMINHO BASE DO PROJETO
# =====================================
# BASE_DIR aponta para a raiz do projeto Django
# Exemplo: .../conecta_fatec/
BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================
# CONFIGURAÇÕES BÁSICAS
# =====================================
SECRET_KEY = 'django-insecure-2!9v#s0zm&#u#@#@+=qha5344ltfl8kh0!q*)zk6=wifo&vt@!'
DEBUG = True

# Durante os testes locais, podemos deixar vazio
# Depois, em produção, isso deve ser ajustado
ALLOWED_HOSTS = ['*']


# =====================================
# APLICAÇÕES INSTALADAS
# =====================================
INSTALLED_APPS = [
    'cloudinary_storage',
    # Apps padrão do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary',
    # Apps de terceiros
    'corsheaders',          # libera requisições do frontend para a API
    'rest_framework',       # base da API REST

    # Apps do projeto
    'users',
    'posts',
    'email_verification',
]


# =====================================
# MIDDLEWARE
# =====================================
MIDDLEWARE = [
    # CORS deve vir o mais alto possível para liberar o frontend local.
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # Vamos manter o CSRF por enquanto.
    # Para JWT usado via frontend puro, ele não atrapalha as rotas da API
    # se estivermos usando Authorization: Bearer <token>
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =====================================
# CONFIGURAÇÃO DE URLS E TEMPLATES
# =====================================
ROOT_URLCONF = 'conecta_fatec.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Mantemos vazio porque seus templates estão nos apps
        'DIRS': [],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'conecta_fatec.wsgi.application'

# ==========================================
# BANCO DE DADOS (SQLite Local / Postgres Nuvem)
# ==========================================
DATABASES = {
    'default': dj_database_url.config(
        # Se não achar um banco na nuvem, usa o SQLite do seu PC
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}


# =====================================
# VALIDAÇÃO DE SENHA
# =====================================
# Mantemos o mínimo de 8 caracteres, como já era sua regra
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
]


# =====================================
# USUÁRIO PERSONALIZADO
# =====================================
AUTH_USER_MODEL = 'users.CustomUser'


# =====================================
# BACKEND DE AUTENTICAÇÃO
# =====================================
# Mantém o login por email OU nickname
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrNicknameBackend',
]


# =====================================
# INTERNACIONALIZAÇÃO
# =====================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True


# =====================================
# ARQUIVOS ESTÁTICOS
# =====================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# =====================================
# ARQUIVOS DE MÍDIA
# =====================================
# Fotos de perfil e comunidades continuam funcionando
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# =====================================
# CHAVE PRIMÁRIA PADRÃO
# =====================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =====================================
# DJANGO REST FRAMEWORK
# =====================================
REST_FRAMEWORK = {
    # Autenticação principal da API
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Permissão padrão:
    # rotas públicas podem usar AllowAny diretamente nas views
    # rotas privadas usarão IsAuthenticated
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}


# =====================================
# JWT (TOKEN)
# =====================================
SIMPLE_JWT = {
    # Token de acesso dura 60 minutos
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),

    # Token de refresh dura 7 dias
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Tipo do header:
    # Authorization: Bearer <token>
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# =====================================
# LOGIN DA INTERFACE DO DRF
# =====================================
# Isso é útil para testes no navegador
LOGIN_URL = '/admin/login/'


# =====================================
# CORS
# =====================================
# Durante os testes locais com HTML puro, vamos liberar tudo.
# Depois, se quiser, a gente restringe para domínios específicos.
CORS_ALLOW_ALL_ORIGINS = True


# =====================================
# CSRF EM ORIGENS LOCAIS
# =====================================
# Ajuda quando você testar frontend local depois
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:5500',
    'http://localhost:5500',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]


# ==========================================
# CONFIGURAÇÃO DE NUVEM (De imagens)
# ==========================================

# 1. Linha falsa apenas para enganar a biblioteca antiga e ela não travar
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# 2. Dicionário moderno obrigatório no Django 5 para arquivos
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# =====================================
# VERIFICAÇÃO DE EMAIL INSTITUCIONAL
# =====================================
FATEC_EMAIL_DOMAIN = "@fatec.sp.gov.br"

EMAIL_VERIFICATION_CODE_MINUTES = 10
EMAIL_VERIFICATION_MAX_ATTEMPTS = 5
REGISTRATION_TOKEN_MAX_AGE_SECONDS = 30 * 60


# =====================================
# ENVIO DE EMAIL - BREVO API / SMTP
# =====================================
# Padrão: Brevo via API HTTPS.
# Motivo: hospedagens como Render podem bloquear portas SMTP.
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "brevo").lower()

# Dados usados pela API transacional da Brevo.
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Conecta Fatec")

# Configuração SMTP mantida apenas como fallback.
# Para usar SMTP, defina EMAIL_PROVIDER=smtp no ambiente.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.office365.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = False

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    BREVO_SENDER_EMAIL or EMAIL_HOST_USER or "no-reply@conectafatec.local"
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_TIMEOUT = 10
BREVO_EMAIL_TIMEOUT = int(os.getenv("BREVO_EMAIL_TIMEOUT", "15"))
