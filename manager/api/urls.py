from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views


router = DefaultRouter()

urlpatterns = [
    path('get-token/', views.obtain_auth_token, name='get-token'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
urlpatterns.append(path('', include(router.urls)))
