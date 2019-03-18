from channels.routing import ProtocolTypeRouter, URLRouter
import subscription.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter(
        subscription.routing.websocket_urlpatterns
    )
})
