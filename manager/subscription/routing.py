from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^manager/ws/subscription/$', consumers.SubscriptionConsumer),
]
