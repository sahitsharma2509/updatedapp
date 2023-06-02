import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'up_dated.settings')

print("ASGI server is running...")  

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import up_dated.routing  # replace 'myapp' with the name of your app
import django
from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            up_dated.routing.websocket_urlpatterns
        )
    ),
})

print("ASGI server is running...")  
