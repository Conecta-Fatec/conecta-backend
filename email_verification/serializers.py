from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import EmailVerification
from .services import create_email_verification, make_registration_token

User = get_user_model()


# =====================================
# INICIAR VERIFICAÇÃO
# =====================================
class StartEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "blank": "O email institucional é obrigatório.",
            "required": "O email institucional é obrigatório.",
            "invalid": "Digite um email válido.",
        }
    )

    def validate_email(self, value):
        email = value.strip().lower()
        allowed_domain = getattr(settings, "FATEC_EMAIL_DOMAIN", "@fatec.sp.gov.br")

        if not email.endswith(allowed_domain):
            raise serializers.ValidationError(
                f"Use um email institucional que termine com {allowed_domain}."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Email já cadastrado no nosso site.",
                code="email_already_registered"
            )

        return email

    def create(self, validated_data):
        return create_email_verification(validated_data["email"])


# =====================================
# CONFIRMAR CÓDIGO
# =====================================
class ConfirmEmailVerificationSerializer(serializers.Serializer):
    verification_id = serializers.UUIDField(
        error_messages={
            "required": "A verificação é obrigatória.",
            "invalid": "Verificação inválida.",
        }
    )

    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "blank": "O código é obrigatório.",
            "required": "O código é obrigatório.",
            "min_length": "O código deve ter 6 dígitos.",
            "max_length": "O código deve ter 6 dígitos.",
        }
    )

    def validate_code(self, value):
        code = value.strip()

        if not code.isdigit():
            raise serializers.ValidationError("O código deve conter apenas números.")

        return code

    def validate(self, attrs):
        verification_id = attrs.get("verification_id")
        code = attrs.get("code")

        try:
            verification = EmailVerification.objects.get(
                id=verification_id,
                purpose=EmailVerification.PURPOSE_REGISTER,
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError({
                "verification_id": "Verificação não encontrada."
            })

        if verification.is_registered:
            raise serializers.ValidationError({
                "detail": "Este email já foi usado para cadastro."
            })

        if verification.is_expired:
            raise serializers.ValidationError({
                "detail": "Código expirado. Solicite um novo código."
            })

        if verification.is_locked:
            raise serializers.ValidationError({
                "detail": "Limite de tentativas excedido. Solicite um novo código."
            })

        if not verification.check_code(code):
            verification.attempts += 1
            verification.save(update_fields=["attempts", "updated_at"])

            attempts_left = max(verification.max_attempts - verification.attempts, 0)

            raise serializers.ValidationError({
                "code": "Código inválido.",
                "attempts_left": attempts_left,
            })

        if not verification.confirmed_at:
            verification.confirmed_at = timezone.now()
            verification.save(update_fields=["confirmed_at", "updated_at"])

        attrs["verification"] = verification
        return attrs

    def save(self):
        verification = self.validated_data["verification"]
        registration_token = make_registration_token(verification)

        return {
            "email": verification.email,
            "registration_token": registration_token,
        }