"""
Middleware: в режиме DEBUG отключаем кэширование ответов браузером,
чтобы всегда загружалась актуальная версия сайта.
"""

from django.conf import settings


class DisableBrowserCacheMiddleware:
    """В DEBUG добавляет заголовки, запрещающие кэширование HTML."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEBUG:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
