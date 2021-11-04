"""Define the rules for routing of channels messages (websockets) in the subscirption application."""
from django.conf.urls import url
from subscription.auth import TokenAuthMiddleware
from .consumers import SubscriptionConsumer

websocket_urlpatterns = [
    url(
        r"^manager(.*?)/ws/subscription/?$",
        TokenAuthMiddleware(SubscriptionConsumer.as_asgi()),
    ),
]
"""List of url patterns that match a URL to a Consumer (in this case only 1)."""
