# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


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
import api.views
from api.views import (
    ConfigFileViewSet,
    ControlLocationViewSet,
    EmergencyContactViewSet,
    ExposurelogViewSet,
    ImageTagViewSet,
    NarrativelogViewSet,
    NightReportViewSet,
    ScriptConfigurationViewSet,
    UserViewSet,
)
from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

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
    path(
        "efd/top_timeseries",
        api.views.query_efd_most_recent_timeseries,
        name="EFD-top-timeseries",
    ),
    path("efd/logmessages", api.views.query_efd_logs, name="EFD-logmessages"),
    path("efd/efd_clients", api.views.query_efd_clients, name="EFD-clients"),
    path(
        "reports/m1m3-bump-tests",
        api.views.query_reports_m1m3_bump_tests,
        name="Reports-m1m3-bump-tests",
    ),
    path("tcs/aux", api.views.tcs_aux_command, name="TCS-aux"),
    path("tcs/aux/docstrings", api.views.tcs_aux_docstrings, name="TCS-aux-docstrings"),
    path("tcs/main", api.views.tcs_main_command, name="TCS-main"),
    path(
        "tcs/main/docstrings", api.views.tcs_main_docstrings, name="TCS-main-docstrings"
    ),
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
    path(
        "ole/nightreport/send/<pk>/",
        api.views.ole_send_night_report,
        name="OLE-nightreport-send-report",
    ),
    path(
        "jira/report/<project>/",
        api.views.get_jira_tickets_report,
        name="Jira-tickets-report",
    ),
]
router.register("user", UserViewSet)
router.register("configfile", ConfigFileViewSet)
router.register("emergencycontact", EmergencyContactViewSet)
router.register("imagetag", ImageTagViewSet)
router.register("ole/exposurelog/messages", ExposurelogViewSet, basename="ExposureLogs")
router.register(
    "ole/narrativelog/messages", NarrativelogViewSet, basename="NarrativeLogs"
)
router.register(
    "ole/nightreport/reports", NightReportViewSet, basename="NightReportLogs"
)
router.register("controllocation", ControlLocationViewSet, basename="ControlLocation")
router.register(
    "scriptconfiguration", ScriptConfigurationViewSet, basename="ScriptConfiguration"
)
urlpatterns.append(path("", include(router.urls)))
