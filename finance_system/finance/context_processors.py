# context_processors.py
"""Контекст-процессоры для шаблонов."""
from .models import Notification


def unread_notifications(request):
    """Добавляет количество непрочитанных уведомлений для авторизованного пользователя."""
    if request.user.is_authenticated:
        return {'unread_notifications_count': Notification.objects.filter(user=request.user, is_read=False).count()}
    return {'unread_notifications_count': 0}
