from django.contrib import admin

from .models import EmailVerification


# =====================================
# ADMIN DE VERIFICAÇÃO DE EMAIL
# =====================================
@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "purpose",
        "attempts",
        "max_attempts",
        "expires_at",
        "confirmed_at",
        "registered_at",
        "created_at",
    ]

    search_fields = ["email"]
    list_filter = ["purpose", "confirmed_at", "registered_at", "created_at"]

    readonly_fields = [
        "id",
        "email",
        "code_hash",
        "purpose",
        "attempts",
        "max_attempts",
        "expires_at",
        "confirmed_at",
        "registered_at",
        "created_at",
        "updated_at",
    ]