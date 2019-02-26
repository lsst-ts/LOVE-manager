from django.conf.urls import url
from subscription.auth import TokenAuthMiddleware
from .consumers import SubscriptionConsumer

websocket_urlpatterns = [
    url(
        '^manager/ws/subscription/?$',
        TokenAuthMiddleware(SubscriptionConsumer)
    ),
]
