"""Defines the rules for routing of channels messages (websockets) in the whole project."""
from channels.routing import ProtocolTypeRouter, URLRouter
import subscription.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter(
        subscription.routing.websocket_urlpatterns
    )
})
