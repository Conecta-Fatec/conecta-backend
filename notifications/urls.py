from django.urls import path
from .api_views import NotificationListAPIView, MarkNotificationAsReadAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkNotificationAsReadAPIView.as_view(), name='notification-read'),
]