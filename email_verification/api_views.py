from django.conf import settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    StartEmailVerificationSerializer,
    ConfirmEmailVerificationSerializer,
    StartPasswordResetVerificationSerializer,
    ConfirmPasswordResetVerificationSerializer,
)


# =====================================
# INICIAR VERIFICAÇÃO DE EMAIL
# =====================================
class StartEmailVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StartEmailVerificationSerializer(data=request.data)

        if serializer.is_valid():
            verification = serializer.save()

            return Response(
                {
                    "message": "Código de verificação enviado para o email institucional.",
                    "verification_id": str(verification.id),
                    "expires_in_seconds": getattr(settings, "EMAIL_VERIFICATION_CODE_MINUTES", 10) * 60,
                },
                status=status.HTTP_200_OK
            )

        email_errors = serializer.errors.get("email")

        if email_errors:
            first_error = email_errors[0]

            if getattr(first_error, "code", None) == "email_already_registered":
                return Response(
                    {
                        "code": "email_already_registered",
                        "message": "Email já cadastrado no nosso site.",
                        "actions": ["back", "forgot_password"],
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# CONFIRMAR CÓDIGO DE EMAIL
# =====================================
class ConfirmEmailVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmEmailVerificationSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()

            return Response(
                {
                    "message": "Email verificado com sucesso.",
                    "email": data["email"],
                    "registration_token": data["registration_token"],
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# INICIAR VERIFICAÇÃO PARA RECUPERAÇÃO DE SENHA
# =====================================
class StartPasswordResetVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StartPasswordResetVerificationSerializer(data=request.data)

        if serializer.is_valid():
            verification = serializer.save()

            return Response(
                {
                    "message": "Código de verificação enviado para o email institucional.",
                    "verification_id": str(verification.id),
                    "expires_in_seconds": getattr(settings, "EMAIL_VERIFICATION_CODE_MINUTES", 10) * 60,
                },
                status=status.HTTP_200_OK
            )

        email_errors = serializer.errors.get("email")

        if email_errors:
            first_error = email_errors[0]
            error_code = getattr(first_error, "code", None)

            if error_code == "email_not_registered":
                return Response(
                    {
                        "code": "email_not_registered",
                        "message": "Email não cadastrado.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if error_code == "password_recently_changed":
                return Response(
                    {
                        "code": "password_recently_changed",
                        "message": "Usuário trocou a senha recentemente.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================
# CONFIRMAR CÓDIGO PARA RECUPERAÇÃO DE SENHA
# =====================================
class ConfirmPasswordResetVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmPasswordResetVerificationSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()

            return Response(
                {
                    "message": "Código verificado com sucesso.",
                    "email": data["email"],
                    "password_reset_token": data["password_reset_token"],
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
