from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

# Trazemos apenas o essencial de quem enviou para não pesar o carregamento
class NotificationSenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'nickname']

class NotificationSerializer(serializers.ModelSerializer):
    sender = NotificationSenderSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'is_read', 'created_at', 'post']