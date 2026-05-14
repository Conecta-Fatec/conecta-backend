from django.urls import path

from .api_views import (
    StartEmailVerificationAPIView,
    ConfirmEmailVerificationAPIView,
)


# =====================================
# ROTAS DE VERIFICAÇÃO DE EMAIL
# =====================================
urlpatterns = [
    path("start/", StartEmailVerificationAPIView.as_view(), name="start-email-verification"),
    path("confirm/", ConfirmEmailVerificationAPIView.as_view(), name="confirm-email-verification"),
]