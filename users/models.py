from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.utils import timezone
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
import sys

# =====================================
# MANAGER PERSONALIZADO (CRIAÇÃO DE USUÁRIO)
# =====================================
class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Cria usuário comum usando email como identificador"""
        if not email:
            raise ValueError("O email é obrigatório")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Cria superusuário com permissões administrativas"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


# =====================================
# MODELO DE USUÁRIO
# =====================================
class CustomUser(AbstractUser):
    username = None  # remove username padrão

   # ---------------------------------
    # OPÇÕES DE CURSO
    # ---------------------------------
    COURSE_CHOICES = [
        ("", "Selecione seu curso"),
        ("Automação Industrial", "Automação Industrial"),
        ("Desenvolvimento de Software Multiplataforma", "Desenvolvimento de Software Multiplataforma"),
        ("Fabricação Mecânica", "Fabricação Mecânica"),
        ("Manutenção Industrial", "Manutenção Industrial"),
        ("Mecânica: Processos de Soldagem", "Mecânica: Processos de Soldagem"),
        ("Refrigeração, Ventilação e Ar Condicionado", "Refrigeração, Ventilação e Ar Condicionado"),
    ]

    # ---------------------------------
    # CAMPOS PRINCIPAIS
    # ---------------------------------
    first_name = models.CharField(max_length=30, verbose_name="Nome")
    last_name = models.CharField(max_length=30, verbose_name="Sobrenome")
    nickname = models.CharField(max_length=30, unique=True, verbose_name="Nickname")
    email = models.EmailField(unique=True, verbose_name="Email institucional")

    # Mantido para compatibilidade com o frontend antigo.
    # A regra real agora usa nickname_changes_count + nickname_change_window_started_at.
    nickname_editable = models.BooleanField(default=True)
    nickname_changes_count = models.PositiveSmallIntegerField(default=0)
    nickname_change_window_started_at = models.DateTimeField(blank=True, null=True)

    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    course = models.CharField(max_length=100, choices=COURSE_CHOICES, blank=True)
    bio = models.CharField(max_length=150, blank=True)

    # ---------------------------------
    # CONFIGURAÇÃO DE LOGIN
    # ---------------------------------
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "nickname"]

    objects = CustomUserManager()

    def __str__(self):
        return self.nickname

    # ---------------------------------
    # REGRAS DE ALTERAÇÃO DE NICKNAME
    # ---------------------------------
    NICKNAME_CHANGE_LIMIT = 2
    NICKNAME_CHANGE_WINDOW_DAYS = 20

    def get_nickname_change_status(self):
        """Retorna o estado atual da janela de alteração de nickname."""
        now = timezone.now()
        window_start = self.nickname_change_window_started_at

        if not window_start:
            used = 0
            next_reset_at = None
        else:
            next_reset_at = window_start + timedelta(days=self.NICKNAME_CHANGE_WINDOW_DAYS)

            if now >= next_reset_at:
                used = 0
                next_reset_at = None
            else:
                used = self.nickname_changes_count

        remaining = max(0, self.NICKNAME_CHANGE_LIMIT - used)

        return {
            "limit": self.NICKNAME_CHANGE_LIMIT,
            "used": used,
            "remaining": remaining,
            "can_change": remaining > 0,
            "next_reset_at": next_reset_at,
        }

    def can_change_nickname(self):
        """Informa se o usuário ainda pode alterar o nickname na janela atual."""
        return self.get_nickname_change_status()["can_change"]

    def register_nickname_change(self):
        """Registra uma alteração de nickname dentro da janela de 20 dias."""
        now = timezone.now()
        status = self.get_nickname_change_status()

        if status["used"] == 0:
            self.nickname_change_window_started_at = now
            self.nickname_changes_count = 1
        else:
            self.nickname_changes_count = status["used"] + 1

        # Atualiza o booleano antigo apenas para não quebrar retornos antigos.
        self.nickname_editable = self.nickname_changes_count < self.NICKNAME_CHANGE_LIMIT

    # =====================================
    # MÉTODOS DE AMIZADE (REGRAS DE NEGÓCIO)
    # =====================================

    def is_friends_with(self, user):
        """Verifica se já são amigos"""
        return Friendship.objects.filter(
            Q(sender=self, receiver=user) | Q(sender=user, receiver=self),
            status=Friendship.ACCEPTED
        ).exists()

    def sent_friend_request_to(self, user):
        """Verifica se enviou solicitação pendente"""
        return Friendship.objects.filter(
            sender=self,
            receiver=user,
            status=Friendship.PENDING
        ).exists()

    def received_friend_request_from(self, user):
        """Verifica se recebeu solicitação pendente"""
        return Friendship.objects.filter(
            sender=user,
            receiver=self,
            status=Friendship.PENDING
        ).exists()

def get_friends(self):
        """Retorna lista de amigos usando a memória do Django (Cache)"""

        amigos_enviados = [
            amizade.receiver 
            for amizade in self.sent_friendships.all() 
            if amizade.status == Friendship.ACCEPTED
        ]

        amigos_recebidos = [
            amizade.sender 
            for amizade in self.received_friendships.all() 
            if amizade.status == Friendship.ACCEPTED
        ]

    return amigos_enviados + amigos_recebidos

    def friends_count(self):
        """Quantidade total de amigos"""
        return len(self.get_friends())
        # =====================================
    # PROCESSAMENTO DE IMAGEM (CORTADOR DE BISCOITOS)
    # =====================================
    
    def save(self, *args, **kwargs):
        # 1. Verifica se existe uma foto E se ela é um arquivo recém-enviado pelo usuário
        if self.photo and isinstance(self.photo.file, UploadedFile):
            try:
                # 2. Abre a imagem que acabou de chegar
                img = Image.open(self.photo)

                # 3. Converte para RGB (PreparaPNGs transparentes para virarem JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # 4. O CORTADOR: Força a imagem a ser um quadrado de 500x500
                tamanho_padrao = (500, 500)
                img = ImageOps.fit(img, tamanho_padrao, Image.Resampling.LANCZOS)

                # 5. Comprime a imagem
                output = BytesIO()
                img.save(output, format='JPEG', quality=70) # Quality 70 reduz o peso drasticamente!
                output.seek(0)

                # 6. Pega o nome original, arranca a extensão velha e coloca .jpg
                nome_original = self.photo.name.split('.')[0]
                novo_nome = f"{nome_original}.jpg"

                # 7. Substitui a imagem pesada pela nova imagem leve e formatada
                self.photo = InMemoryUploadedFile(
                    output, 'ImageField', 
                    novo_nome, 
                    'image/jpeg', sys.getsizeof(output), None
                )
            except Exception as e:
                # Se acontecer algum erro bizarro com a imagem, o Django simplesmente 
                # ignora o corte e salva a imagem original para não quebrar o site
                print(f"Erro ao processar imagem: {e}")

        # 8. Finalmente, chama o comando original do Django para salvar no banco de dados!
        super().save(*args, **kwargs)


# =====================================
# MODELO DE AMIZADE
# =====================================
class Friendship(models.Model):

    # ---------------------------------
    # STATUS
    # ---------------------------------
    PENDING = "pending"
    ACCEPTED = "accepted"

    STATUS_CHOICES = [
        (PENDING, "Pendente"),
        (ACCEPTED, "Aceita"),
    ]

    # ---------------------------------
    # RELACIONAMENTOS
    # ---------------------------------
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sent_friendships"
    )

    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_friendships"
    )

    # ---------------------------------
    # CONTROLE
    # ---------------------------------
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------------------------
    # CONFIGURAÇÕES DO MODEL
    # ---------------------------------
    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_friendship_request"
            )
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"

    def save(self, *args, **kwargs):
        """Impede amizade com si mesmo"""
        if self.sender == self.receiver:
            raise ValueError("Um usuário não pode enviar amizade para si mesmo.")

        super().save(*args, **kwargs)