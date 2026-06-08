from django.urls import path

from .api_views import (
    StartEmailVerificationAPIView,
    ConfirmEmailVerificationAPIView,
    StartPasswordResetVerificationAPIView,
    ConfirmPasswordResetVerificationAPIView,
)


# =====================================
# ROTAS DE VERIFICAÇÃO DE EMAIL
# =====================================
urlpatterns = [
    path("start/", StartEmailVerificationAPIView.as_view(), name="start-email-verification"),
    path("confirm/", ConfirmEmailVerificationAPIView.as_view(), name="confirm-email-verification"),

    # Recuperação de senha
    path("password-reset/start/", StartPasswordResetVerificationAPIView.as_view(), name="start-password-reset-verification"),
    path("password-reset/confirm/", ConfirmPasswordResetVerificationAPIView.as_view(), name="confirm-password-reset-verification"),
]