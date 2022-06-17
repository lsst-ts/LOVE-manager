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
from api.views import (
    ConfigFileViewSet,
    EmergencyContactViewSet,
    ExposurelogViewSet,
    NarrativelogViewSet,
)

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
    path(
        "lovecsc/observinglog",
        api.views.lovecsc_observinglog,
        name="lovecsc-observinglog",
    ),
    path("salinfo/metadata", api.views.salinfo_metadata, name="salinfo-metadata"),
    path(
        "salinfo/topic-names", api.views.salinfo_topic_names, name="salinfo-topic-names"
    ),
    path("salinfo/topic-data", api.views.salinfo_topic_data, name="salinfo-topic-data"),
    path("config", api.views.get_config, name="config"),
    path("config-set", api.views.set_config_selected, name="config-set"),
    path("efd/timeseries", api.views.query_efd_timeseries, name="EFD-timeseries"),
    path("efd/logmessages", api.views.query_efd_logs, name="EFD-logmessages"),
    path("efd/efd_clients", api.views.query_efd_clients, name="EFD-clients"),
    path("tcs/aux", api.views.tcs_aux_command, name="TCS-aux"),
    path("tcs/aux/docstrings", api.views.tcs_aux_docstrings, name="TCS-aux-docstrings"),
    path("tcs/main", api.views.tcs_main_command, name="TCS-main"),
    path(
        "tcs/main/docstrings", api.views.tcs_main_docstrings, name="TCS-main-docstrings"
    ),
    path("jira", api.views.jira, name="JIRA-API"),
    path("lfa/", api.views.lfa, name="LFA-API"),
    path("lfa/<option>/", api.views.lfa, name="LFA-API"),
    path(
        "ole/exposurelog/exposures",
        api.views.ole_exposurelog_exposures,
        name="OLE-exposurelog-exposures",
    ),
    path(
        "ole/exposurelog/instruments",
        api.views.ole_exposurelog_instruments,
        name="OLE-exposurelog-instruments",
    ),
]
router.register("configfile", ConfigFileViewSet)
router.register("emergencycontact", EmergencyContactViewSet)
router.register(
    "authlistrequest",
    api.views.CSCAuthorizationRequestViewSet,
    basename="authlistrequest",
)
router.register("ole/exposurelog/messages", ExposurelogViewSet, basename="ExposureLogs")
router.register(
    "ole/narrativelog/messages", NarrativelogViewSet, basename="NarrativeLogs"
)
urlpatterns.append(path("", include(router.urls)))
