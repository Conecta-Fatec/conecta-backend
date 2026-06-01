from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Puxa apenas as notificações de quem está logado. 
        # O select_related previne aquele gargalo de N+1 queries que já resolvemos antes!
        notifications = Notification.objects.filter(recipient=request.user).select_related('sender')
        
        # Conta quantas têm o is_read=False para pintar o sininho vermelho
        unread_count = notifications.filter(is_read=False).count()
        
        serializer = NotificationSerializer(notifications, many=True, context={'request': request})
        
        return Response({
            'unread_count': unread_count,
            'results': serializer.data
        }, status=status.HTTP_200_OK)

class MarkNotificationAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            # Garante que um usuário não consiga marcar a notificação de outro como lida
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            # Salva apenas o campo is_read para ser mais rápido
            notification.save(update_fields=['is_read'])
            
            return Response({'message': 'Notificação lida com sucesso.'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notificação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)