from django.urls import path
from .consumer import ChatConsumer

websocket_urlpatterns = [
    path('channel/', ChatConsumer.as_asgi()),
]