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

# from api.views import validate_token, logout, CustomObtainAuthToken, validate_config_schema, commander, salinfo_metadata
import api.views

router = DefaultRouter()

urlpatterns = [
    path("get-token/", api.views.CustomObtainAuthToken.as_view(), name="login"),
    path("validate-token/", api.views.validate_token, name="validate-token"),
    path("validate-token/<flags>/", api.views.validate_token, name="validate-token"),
    path(
        "validate-config-schema/",
        api.views.validate_config_schema,
        name="validate-config-schema",
    ),
    path("logout/", api.views.logout, name="logout"),
    path("swap-user/", api.views.CustomSwapAuthToken.as_view(), name="swap-user"),
    path(
        "swap-user/<flags>/", api.views.CustomSwapAuthToken.as_view(), name="swap-user"
    ),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("cmd/", api.views.commander, name="commander"),
    path("lovecsc/", api.views.lovecsc, name="love-csc"),
    path("salinfo/metadata", api.views.salinfo_metadata, name="salinfo-metadata"),
    path(
        "salinfo/topic-names", api.views.salinfo_topic_names, name="salinfo-topic-names"
    ),
    path("salinfo/topic-data", api.views.salinfo_topic_data, name="salinfo-topic-data"),
    path("config", api.views.get_config, name="config"),
]
urlpatterns.append(path("", include(router.urls)))
