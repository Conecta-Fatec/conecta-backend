import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


# =====================================
# VERIFICAÇÃO DE EMAIL
# =====================================
class EmailVerification(models.Model):
    PURPOSE_REGISTER = "register"
    PURPOSE_PASSWORD_RESET = "password_reset"

    PURPOSE_CHOICES = [
        (PURPOSE_REGISTER, "Cadastro"),
        (PURPOSE_PASSWORD_RESET, "Recuperação de senha"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(db_index=True)

    code_hash = models.CharField(max_length=128)

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        default=PURPOSE_REGISTER
    )

    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    expires_at = models.DateTimeField()

    confirmed_at = models.DateTimeField(blank=True, null=True)
    registered_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "created_at"]),
        ]

    def __str__(self):
        return f"{self.email} - {self.purpose}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_confirmed(self):
        return self.confirmed_at is not None

    @property
    def is_registered(self):
        return self.registered_at is not None

    @property
    def is_used(self):
        return self.registered_at is not None

    @property
    def is_locked(self):
        return self.attempts >= self.max_attempts

    def set_code(self, code):
        self.code_hash = make_password(code)

    def check_code(self, code):
        return check_password(code, self.code_hash)