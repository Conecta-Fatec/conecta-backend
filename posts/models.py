from django.conf import settings
from django.db import models
from django.utils.text import slugify


# =====================================
# MODELO DE COMUNIDADE
# =====================================
class Community(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_communities",
        verbose_name="Criador"
    )

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nome"
    )

    slug = models.SlugField(
        max_length=60,
        unique=True,
        verbose_name="Slug"
    )

    description = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Descrição"
    )

    photo = models.ImageField(
        upload_to="community_photos/",
        blank=True,
        null=True,
        verbose_name="Foto da comunidade"
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="communities",
        blank=True,
        verbose_name="Membros"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Comunidade"
        verbose_name_plural = "Comunidades"

    def __str__(self):
        return self.name

    def total_members(self):
        return self.members.count()

    def save(self, *args, **kwargs):
        """
        Gera slug automaticamente a partir do nome da comunidade.
        """
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)


# =====================================
# MODELO DE POST
# =====================================
class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Autor"
    )

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Comunidade"
    )

    content = models.CharField(
        max_length=200,
        blank=True, 
        null=True,
        verbose_name="Conteúdo"
    )

    gif_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL do GIF"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_posts",
        blank=True,
        verbose_name="Curtidas"
    )

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        if self.community:
            return f"Post de {self.author.nickname} em {self.community.name} - {self.content[:30]}"
        return f"Post de {self.author.nickname} - {self.content[:30]}"


# =====================================
# MODELO DE COMENTÁRIO
# =====================================
class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Autor"
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Post",
        blank=True,
        null=True
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Comentário pai",
        blank=True,
        null=True
    )

    content = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Conteúdo"
    )

    gif_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL do GIF"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    edited = models.BooleanField(
        default=False,
        verbose_name="Editado"
    )

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_comments",
        blank=True,
        verbose_name="Curtidas"
    )

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return f"Comentário de {self.author.nickname} - {self.content[:30]}"