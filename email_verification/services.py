import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import dumps, loads
from django.utils import timezone

from .models import EmailVerification


# =====================================
# CONFIGURAÇÕES INTERNAS
# =====================================
REGISTRATION_TOKEN_SALT = "conecta_fatec.registration_token"


# =====================================
# GERAR CÓDIGO
# =====================================
def generate_verification_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


# =====================================
# ENVIAR EMAIL
# =====================================
def send_verification_email(email, code):
    provider = getattr(settings, "EMAIL_PROVIDER", "brevo").lower()

    if provider == "brevo":
        return send_verification_email_brevo(email, code)

    return send_verification_email_smtp(email, code)


# =====================================
# ENVIAR EMAIL VIA SMTP - FALLBACK
# =====================================
def send_verification_email_smtp(email, code):
    minutes = getattr(settings, "EMAIL_VERIFICATION_CODE_MINUTES", 10)

    subject = "Código de verificação - Conecta Fatec"

    message = (
        "Olá!\n\n"
        "Recebemos uma solicitação de cadastro no Conecta Fatec.\n\n"
        f"Seu código de verificação é: {code}\n\n"
        f"Este código é válido por {minutes} minutos.\n\n"
        "Se você não solicitou este cadastro, ignore este e-mail.\n\n"
        "Conecta Fatec"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


# =====================================
# ENVIAR EMAIL VIA BREVO API
# =====================================
def send_verification_email_brevo(email, code):
    import requests

    minutes = getattr(settings, "EMAIL_VERIFICATION_CODE_MINUTES", 10)

    api_key = getattr(settings, "BREVO_API_KEY", None)
    sender_email = getattr(settings, "BREVO_SENDER_EMAIL", None)
    sender_name = getattr(settings, "BREVO_SENDER_NAME", "Conecta Fatec")
    timeout = getattr(settings, "BREVO_EMAIL_TIMEOUT", 15)

    if not api_key:
        raise RuntimeError("BREVO_API_KEY não configurada no backend.")

    if not sender_email:
        raise RuntimeError("BREVO_SENDER_EMAIL não configurado no backend.")

    subject = "Código de verificação - Conecta Fatec"

    text_content = (
        "Olá!\n\n"
        "Recebemos uma solicitação de cadastro no Conecta Fatec.\n\n"
        f"Seu código de verificação é: {code}\n\n"
        f"Este código é válido por {minutes} minutos.\n\n"
        "Se você não solicitou este cadastro, ignore este e-mail.\n\n"
        "Conecta Fatec"
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5;">
        <h2>Código de verificação - Conecta Fatec</h2>

        <p>Olá!</p>

        <p>Recebemos uma solicitação de cadastro no Conecta Fatec.</p>

        <p>Seu código de verificação é:</p>

        <p style="font-size: 28px; font-weight: bold; letter-spacing: 4px;">
          {code}
        </p>

        <p>Este código é válido por {minutes} minutos.</p>

        <p>Se você não solicitou este cadastro, ignore este e-mail.</p>

        <p>Conecta Fatec</p>
      </body>
    </html>
    """

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": email,
            }
        ],
        "subject": subject,
        "textContent": text_content,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise RuntimeError("Não foi possível conectar à API da Brevo para enviar o email.") from error

    if response.status_code >= 400:
        raise RuntimeError(f"Erro ao enviar email pela Brevo: {response.text}")

    if response.content:
        return response.json()

    return None


# =====================================
# CRIAR VERIFICAÇÃO
# =====================================
def create_email_verification(email):
    code = generate_verification_code()

    minutes = getattr(settings, "EMAIL_VERIFICATION_CODE_MINUTES", 10)
    max_attempts = getattr(settings, "EMAIL_VERIFICATION_MAX_ATTEMPTS", 5)

    expires_at = timezone.now() + timedelta(minutes=minutes)

    # Remove códigos antigos ainda não confirmados para o mesmo email.
    EmailVerification.objects.filter(
        email__iexact=email,
        purpose=EmailVerification.PURPOSE_REGISTER,
        confirmed_at__isnull=True,
        registered_at__isnull=True,
    ).delete()

    verification = EmailVerification(
        email=email,
        purpose=EmailVerification.PURPOSE_REGISTER,
        max_attempts=max_attempts,
        expires_at=expires_at,
    )

    verification.set_code(code)
    verification.save()

    send_verification_email(email, code)

    return verification


# =====================================
# CRIAR TOKEN TEMPORÁRIO DE CADASTRO
# =====================================
def make_registration_token(verification):
    payload = {
        "verification_id": str(verification.id),
        "email": verification.email,
        "purpose": verification.purpose,
    }

    return dumps(payload, salt=REGISTRATION_TOKEN_SALT)


# =====================================
# LER TOKEN TEMPORÁRIO DE CADASTRO
# =====================================
def read_registration_token(token):
    max_age = getattr(settings, "REGISTRATION_TOKEN_MAX_AGE_SECONDS", 30 * 60)

    return loads(
        token,
        salt=REGISTRATION_TOKEN_SALT,
        max_age=max_age,
    )