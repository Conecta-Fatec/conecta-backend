from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = [
        ('like', 'Curtida no Post'),
        ('comment', 'Comentário no Post'),
        ('friend_request', 'Solicitação de Amizade'),
        ('friend_accept', 'Amizade Aceita'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] 
        
    def __str__(self):
        return f"{self.sender} -> {self.recipient} ({self.notification_type})"