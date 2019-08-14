"""API app URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/

Examples
--------
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from api.views import validate_token, logout, CustomObtainAuthToken


router = DefaultRouter()

urlpatterns = [
    path('get-token/', CustomObtainAuthToken.as_view(), name='login'),
    path('validate-token/', validate_token, name='validate-token'),
    path('logout/', logout, name='logout'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
urlpatterns.append(path('', include(router.urls)))
