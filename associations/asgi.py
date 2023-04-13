"""
ASGI config for associations project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

from game.routing import websocket_urlpatterns
from game.token_auth import TokenAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'associations.settings')
django.setup()

application = ProtocolTypeRouter({
  'http': get_asgi_application(),
  'websocket': TokenAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
})