from django.conf import settings


class HostBasedUrlconfMiddleware:
    """Selecciona el urlconf segun el host: el subdominio de gestion usa
    cesfam_chatbot.urls_gestion; cualquier otro host usa el ROOT_URLCONF."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host == settings.GESTION_HOST.lower():
            request.urlconf = "cesfam_chatbot.urls_gestion"
        return self.get_response(request)
