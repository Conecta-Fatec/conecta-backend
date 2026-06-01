from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

# Importamos os modelos do seu projeto
from posts.models import Comment, Post
from users.models import CustomUser
from .models import Notification

# ==========================================
# 1. NOTIFICAÇÃO DE COMENTÁRIO
# ==========================================
# O post_save "escuta" toda vez que um Comment é salvo no banco
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    # Se o comentário é novo E não foi o próprio autor do post que comentou
    if created and instance.post.author != instance.author:
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type='comment',
            post=instance.post
        )

# ==========================================
# 2. NOTIFICAÇÃO DE CURTIDA
# ==========================================
# O m2m_changed "escuta" toda vez que a lista de likes (Many-To-Many) muda
@receiver(m2m_changed, sender=Post.likes.through)
def create_like_notification(sender, instance, action, pk_set, **kwargs):
    # "post_add" significa que alguém acabou de ser adicionado à lista de likes
    if action == "post_add":
        for user_id in pk_set:
            sender_user = CustomUser.objects.get(pk=user_id)
            
            # Só notifica se a pessoa não estiver curtindo o próprio post
            if sender_user != instance.author:
                Notification.objects.create(
                    recipient=instance.author,
                    sender=sender_user,
                    notification_type='like',
                    post=instance
                )