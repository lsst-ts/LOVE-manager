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


"""Defines the views exposed by the REST API exposed by this app."""
import collections
import json
import os
import urllib

import astropy.time
import jsonschema
import ldap
import requests
import yaml
from api.models import (
    ConfigFile,
    ControlLocation,
    EmergencyContact,
    ImageTag,
    ScriptConfiguration,
    Token,
)
from api.serializers import (
    ConfigFileContentSerializer,
    ConfigFileSerializer,
    ConfigSerializer,
    ControlLocationSerializer,
    EmergencyContactSerializer,
    ImageTagSerializer,
    ScriptConfigurationSerializer,
    TokenSerializer,
    UserSerializer,
)
from django.contrib.auth.models import Group, User
from django_auth_ldap.backend import LDAPBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from manager.settings import (
    AUTH_LDAP_1_SERVER_URI,
    AUTH_LDAP_2_SERVER_URI,
    AUTH_LDAP_3_SERVER_URI,
)
from manager.utils import (
    CommandPermission,
    arrange_nightreport_email,
    get_jira_obs_report,
    get_obsday_from_tai,
    get_obsday_iso,
    handle_jira_payload,
    send_smtp_email,
    upload_to_lfa,
)

from .schema_validator import DefaultingValidator

valid_response = openapi.Response("Valid token", TokenSerializer)
invalid_response = openapi.Response("Invalid token")
not_found_response = openapi.Response("Not found")


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response("Valid token", TokenSerializer),
        401: openapi.Response("Invalid token"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def validate_token(request, *args, **kwargs):
    """Validate the token and return 200 code if valid.

    If the token is invalid this function is not executed
    (the request fails before)


    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currenlty unused
    kwargs: dict
        Dictionary with addittional keyword arguments
        (indexed by keys in the dict), one optional parameter
        that could be expeted is `flags`

    Returns
    -------
    Response
        The response stating that the token is valid
        with a 200 status code.
    """
    flags = kwargs.get("flags", None)
    no_config = flags == "no_config" or flags == "no-config"
    token_key = request.META.get("HTTP_AUTHORIZATION")[6:]
    token = Token.objects.get(key=token_key)
    data = TokenSerializer(
        token,
        context={
            "no_config": no_config,
            "request": request,
        },
    ).data
    return Response(data)


@swagger_auto_schema(
    method="delete", responses={204: openapi.Response("Logout Successful")}
)
@api_view(["DELETE"])
@permission_classes((IsAuthenticated,))
def logout(request):
    """Logout and delete the token. And returns 204 code if valid.

    If the token is invalid this function is not executed
    (the request fails before)

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response stating that the token has been deleted,
        with a 204 status code.
    """
    token = request._auth
    token.delete()
    return Response(
        {"detail": "Logout successful, Token succesfully deleted"},
        status=status.HTTP_204_NO_CONTENT,
    )


class IPABackend1(LDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    successful_login = False

    def authenticate_ldap_user(self, ldap_user, password):
        user = ldap_user.authenticate(password)
        if user:
            IPABackend1.successful_login = True
        return user


class IPABackend2(LDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    successful_login = False

    def authenticate_ldap_user(self, ldap_user, password):
        user = ldap_user.authenticate(password)
        if user:
            IPABackend2.successful_login = True
        return user


class IPABackend3(LDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"
    successful_login = False

    def authenticate_ldap_user(self, ldap_user, password):
        user = ldap_user.authenticate(password)
        if user:
            IPABackend3.successful_login = True
        return user


class CustomObtainAuthToken(ObtainAuthToken):
    """API endpoint to obtain authorization tokens.

    This method will try first to authenticate the user againts LDAP servers.
    If authentication fails againts LDAP servers, the authentication
    will be done againts local database.

    If trying to authenticate with a LDAP user for the first time, if login
    succeeds and if user is part of love_ops group,
    then cmd permissions are added.

    """

    login_response = openapi.Response("Login succesful", TokenSerializer)
    login_failed_response = openapi.Response("Login failed")

    @swagger_auto_schema(responses={200: login_response, 400: login_failed_response})
    def post(self, request, *args, **kwargs):
        """Handle the (post) request for token.

        If the token is invalid this function is not executed
        (the request fails before)

        Params
        ------
        request: Request
            The Request object
        args: list
            List of addittional arguments. Currenlty unused
        kwargs: dict
            Dictionary with addittional keyword arguments
            (indexed by keys in the dict). Currenlty unused

        Returns
        -------
        Response
            The response containing the token and other user data.
        """
        username = request.data["username"]
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.validated_data["user"]

        ldap_result = None
        if IPABackend1.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_1_SERVER_URI)
        elif IPABackend2.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_2_SERVER_URI)
        elif IPABackend3.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_3_SERVER_URI)

        baseDN = "cn=love_ops,cn=groups,cn=compat,dc=lsst,dc=cloud"
        searchScope = ldap.SCOPE_SUBTREE

        if ldap_result is not None:
            try:
                ldap_result = ldap_result.search_s(baseDN, searchScope)
                ops_users = list(
                    map(lambda u: u.decode(), ldap_result[0][1]["memberUid"])
                )
                if username in ops_users:
                    cmd_group = Group.objects.filter(name="cmd").first()
                    ui_framework_group = Group.objects.filter(
                        name="ui_framework"
                    ).first()
                    cmd_group.user_set.add(user_obj)
                    ui_framework_group.user_set.add(user_obj)
            except Exception:
                data = {
                    "detail": "Login failed, add cmd and ui_framework permissions error."
                }
                return Response(data, status=400)

        token = Token.objects.create(user=user_obj)
        request.user = (
            user_obj  # This is required to pass a logged user to the serializer
        )
        return Response(TokenSerializer(token, context={"request": request}).data)


class CustomSwapAuthToken(ObtainAuthToken):
    """API endpoint to swap authorization tokens.

    This method will try first to authenticate the user againts LDAP servers.
    If authentication fails againts LDAP servers, the authentication
    will be done againts local database.

    If trying to authenticate with a LDAP user for the first time, if login
    succeeds and if user is part of love_ops group,
    then cmd permissions are added.
    """

    login_response = openapi.Response("User swap succesful", TokenSerializer)
    login_failed_response = openapi.Response("User swap failed")

    @swagger_auto_schema(responses={200: login_response, 400: login_failed_response})
    @permission_classes((IsAuthenticated,))
    def post(self, request, *args, **kwargs):
        """Handle the (post) request for token.

        If the token is invalid this function is not executed
        (the request fails before)

        Params
        ------
        request: Request
            The Request object
        args: list
            List of addittional arguments. Currently unused
        kwargs: dict
            Dictionary with addittional keyword arguments
            (indexed by keys in the dict). Currenlty unused

        Returns
        -------
        Response
            The response containing the token and other user data.
        """
        username = request.data["username"]
        if not request.user.is_authenticated or not request._auth:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.validated_data["user"]

        ldap_result = None
        if IPABackend1.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_1_SERVER_URI)
        elif IPABackend2.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_2_SERVER_URI)
        elif IPABackend3.successful_login:
            ldap_result = ldap.initialize(AUTH_LDAP_3_SERVER_URI)

        baseDN = "cn=love_ops,cn=groups,cn=compat,dc=lsst,dc=cloud"
        searchScope = ldap.SCOPE_SUBTREE

        if ldap_result is not None:
            try:
                ldap_result = ldap_result.search_s(baseDN, searchScope)
                ops_users = list(
                    map(lambda u: u.decode(), ldap_result[0][1]["memberUid"])
                )
                if username in ops_users:
                    cmd_group = Group.objects.filter(name="cmd").first()
                    ui_framework_group = Group.objects.filter(
                        name="ui_framework"
                    ).first()
                    cmd_group.user_set.add(user_obj)
                    ui_framework_group.user_set.add(user_obj)
            except Exception:
                data = {
                    "detail": "Login failed, add cmd and ui_framework permissions error."
                }
                return Response(data, status=400)

        token = Token.objects.create(user=user_obj)
        old_token = request._auth
        old_token.delete()

        flags = kwargs.get("flags", None)
        no_config = flags == "no_config" or flags == "no-config"

        request.user = (
            user_obj  # This is required to pass a logged user to the serializer
        )
        return Response(
            TokenSerializer(
                token,
                context={"no_config": no_config, "request": request},
            ).data
        )


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def validate_config_schema(request):
    """Validate a configuration yaml with using a schema

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        Dictionary containing a 'title' and an 'error' key (if any)
        or an 'output' with the output of the validator
        (config with defaults-autocomplete)
    """
    try:
        config = yaml.safe_load(request.data["config"])
    except yaml.YAMLError as e:
        error = e.__dict__
        error["problem_mark"] = e.problem_mark.__dict__
        del error["context_mark"]
        return Response({"title": "ERROR WHILE PARSING YAML STRING", "error": error})
    schema = yaml.safe_load(request.data["schema"])
    validator = DefaultingValidator(schema)

    try:
        output = validator.validate(config)
        return Response({"title": "None", "output": output})
    except jsonschema.exceptions.ValidationError as e:
        error = e.__dict__
        for key in error:
            if isinstance(error[key], collections.deque):
                error[key] = list(error[key])

        return Response(
            {
                "title": "INVALID CONFIG YAML",
                "error": {
                    "message": str(error["message"]),
                    "path": [] if not error["path"] else list(error["path"]),
                    "schema_path": (
                        [] if not error["schema_path"] else list(error["schema_path"])
                    ),
                },
            }
        )


@swagger_auto_schema(
    method="post",
    responses={
        200: openapi.Response("Command sent"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["POST"])
@permission_classes((IsAuthenticated, CommandPermission))
def commander(request):
    """Sends a command to the LOVE-commander
    according to the received parameters

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/cmd"
    response = requests.post(url, json=request.data)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="post",
    responses={
        200: openapi.Response("Observing log sent"),
        400: openapi.Response("Missing parameters"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["POST"])
@permission_classes((IsAuthenticated, CommandPermission))
def lovecsc_observinglog(request):
    """Sends an observing log message to the LOVE-commander
    according to the received parameters

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:"
        f"{os.environ.get('COMMANDER_PORT')}/lovecsc/observinglog"
    )
    response = requests.post(url, json=request.data)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            "Response of the form: "
            + json.dumps(
                {"<csc_name>": {"sal_version": "x.x.x", "xml_version": "x.x.x"}},
                indent=4,
            )
        ),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def salinfo_metadata(request):
    """Requests SalInfo.metadata from the commander containing a dict
    of <csc name>: { "sal_version": ..., "xml_version": ....}

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/salinfo/metadata"
    response = requests.get(url)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            "Response of the form: "
            + json.dumps(
                {
                    "<csc_name>": {
                        "command_names": [],
                        "event_names": [],
                        "telemetry_names": [],
                    }
                },
                indent=4,
            )
        ),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def salinfo_topic_names(request):
    """Requests SalInfo.topic_names from the commander containing a dict
    of <csc name>:
    { "command_names": [], "event_names": [], "telemetry_names": []}

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    query = ""
    if "categories" in request.query_params:
        query = "?categories=" + request.query_params["categories"]
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:"
        f"{os.environ.get('COMMANDER_PORT')}/salinfo/topic-names{query}"
    )
    response = requests.get(url)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response(
            "Response of the form: "
            + json.dumps(
                {
                    "<csc_name>": {
                        "command_data": [],
                        "event_data": [],
                        "telemetry_data": [],
                    }
                },
                indent=4,
            )
        ),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def salinfo_topic_data(request):
    """Requests SalInfo.topic_data from the commander containing a dict
     of <csc name>:
     { "command_data": [], "event_data": [], "telemetry_data": []}

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    query = ""
    if "categories" in request.query_params:
        query = "?categories=" + request.query_params["categories"]
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:"
        f"{os.environ.get('COMMANDER_PORT')}/salinfo/topic-data{query}"
    )
    response = requests.get(url)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response("Config file", ConfigSerializer),
        401: openapi.Response("Unauthenticated"),
        404: not_found_response,
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def get_config(request):
    """Returns the config file

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        Containing the contents of the config file
    """
    try:
        cf = ConfigFile.objects.first()
    except ConfigFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ConfigFileContentSerializer(cf)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    responses={
        200: openapi.Response("Config file", ConfigSerializer),
        401: openapi.Response("Unauthenticated"),
        404: not_found_response,
    },
)
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def set_config_selected(request):
    """Adds the current User to the selected_by_users
    of the specified Config file

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        Containing the contents of the config file
    """

    try:
        configuration_to_update = ConfigFile.objects.get(
            pk=request.data.get("config_id")
        )
        current_user = request.user
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    configuration_files_qs = ConfigFile.objects.filter(selected_by_users=current_user)
    for config in configuration_files_qs:
        config.selected_by_users.remove(current_user)
        config.save()
    configuration_to_update.selected_by_users.add(current_user)
    configuration_to_update.save()

    serializer = ConfigFileContentSerializer(configuration_to_update)
    return Response(serializer.data)


class ConfigFileViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the ConfigFile model."""

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = ConfigFile.objects.order_by("-update_timestamp").all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = ConfigFileSerializer
    """Serializer used to serialize View objects"""

    @action(detail=True)
    def content(self, request, pk=None):
        """Serialize a ConfigFile's content.

        Params
        ------
        request: Request
            The Requets object
        pk: int
            The corresponding ConfigFile pk

        Returns
        -------
        Response
            The response containing the serialized ConfigFile content
        """

        try:
            cf = ConfigFile.objects.get(pk=pk)
        except ConfigFile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            serializer_data = ConfigFileContentSerializer(cf).data
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer_data)


class UserViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances of the User model."""

    permission_classes = [
        IsAuthenticated,
    ]

    # TODO: once the default users are removed,
    # the following code must be adjusted.
    # See: DM-43181.
    excluded_usernames = ["admin", "cmd_user", "test", "user"]
    queryset = User.objects.exclude(username__in=excluded_usernames)
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = UserSerializer
    """Serializer used to serialize View objects"""


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the EmergencyContact model."""

    queryset = EmergencyContact.objects.order_by("subsystem").all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = EmergencyContactSerializer
    """Serializer used to serialize View objects"""


class ImageTagViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances of the ImageTag model."""

    queryset = ImageTag.objects.order_by("label").all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = ImageTagSerializer
    """Serializer used to serialize View objects"""


@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def query_efd_clients(request):
    """Requests EFD instances

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/efd/efd_clients"
    response = requests.get(url)

    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def query_efd_timeseries(request, *args, **kwargs):
    """Queries data from an EFD timeseries
    by redirecting the request to the Commander

    Params
    ------
    request: Request
        The Request object
        Dictionary with request arguments.
        Request should contain the following:
            start_date (required): String specifying
            the start of the query range.
            Default current date minus 10 minutes
            timewindow (required): Int specifying
            the number of minutes to query starting from start_date.
            Default 10
            topics (required): Dictionary of the form
                {
                    CSC1: {
                        index: [topic1, topic2...],
                    },
                    CSC2: {
                        index: [topic1, topic2...],
                    },
                }
            resample (optional): The offset string representing target
                resample conversion, e.g. '15min', '10S'
            efd_instance (required): The specific EFD instance to query
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dict of additional arguments. Currently unused

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/efd/timeseries"
    response = requests.post(url, json=request.data)
    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def query_efd_logs(request, *args, **kwargs):
    """Queries data from an EFD timeseries by
    redirecting the request to the Commander

    Params
    ------
    request: Request
        The Request object
        Dictionary with request arguments.
        Request should contain the following:
            start_date (required): String specifying
            the start of the query range.
            end_date (required): String specifying
            the end of the query range.
            cscs (required): Dictionary of the form
                {
                    CSC1: {
                        index: [topic1, topic2...],
                    },
                    CSC2: {
                        index: [topic1, topic2...],
                    },
                }
            efd_instance (required): The specific EFD instance to query
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dict of additional arguments. Currently unused

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/efd/logmessages"
    response = requests.post(url, json=request.data)
    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def query_reports_m1m3_bump_tests(request):
    """Requests M1M3 bump tests reports

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:"
        f"{os.environ.get('COMMANDER_PORT')}/reports/m1m3-bump-tests"
    )
    response = requests.post(url, json=request.data)

    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated, CommandPermission))
def tcs_aux_command(request, *args, **kwargs):
    """Sends command to the ATCS

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments.
        Request should contain the following:
            command_name (required): The name of the command to be run.
            It should be a field of the
            lsst.ts.observatory.control.auxtel.ATCS class
            params (required): Parameters to be passed
            to the command method, e.g.
                {
                    ra: 80,
                    dec: 30,
                }

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/tcs/aux"
    response = requests.post(url, json=request.data)
    return Response(response.json(), status=response.status_code)


@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def tcs_aux_docstrings(request, *args, **kwargs):
    """Requests ATCS commands docstrings

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments. Currently unused

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}"
        f":{os.environ.get('COMMANDER_PORT')}/tcs/aux/docstrings"
    )
    response = requests.get(url)
    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated, CommandPermission))
def tcs_main_command(request, *args, **kwargs):
    """Sends command to the MTCS

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments.
        Request should contain the following:
            command_name (required): The name of the command to be run.
            It should be a field of the
            lsst.ts.observatory.control.maintel.MTCS class
            params (required): Parameters to be passed
            to the command method, e.g.
                {
                    ra: 80,
                    dec: 30,
                }

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/tcs/main"
    response = requests.post(url, json=request.data)
    return Response(response.json(), status=response.status_code)


@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def tcs_main_docstrings(request, *args, **kwargs):
    """Requests TCS commands docstrings

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments. Currently unused

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    url = (
        f"http://{os.environ.get('COMMANDER_HOSTNAME')}:"
        f"{os.environ.get('COMMANDER_PORT')}/tcs/main/docstrings"
    )
    response = requests.get(url)
    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response("Exposures received"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def ole_exposurelog_exposures(request, *args, **kwargs):
    """Connects to Open API exposurelog service and get the list of exposures

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request
        to the Open API exposurelog service
    """

    query_params_string = urllib.parse.urlencode(request.query_params)
    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/exposures?{query_params_string}"
    response = requests.get(url, json=request.data)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="get",
    responses={
        200: openapi.Response("Instruments received"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def ole_exposurelog_instruments(request):
    """Connects to Open API exposurelog service and get the list of instruments

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request
        to the Open API exposurelog service
    """

    query_params_string = urllib.parse.urlencode(request.query_params)
    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/instruments?{query_params_string}"
    response = requests.get(url, json=request.data)

    return Response(response.json(), status=response.status_code)


class ExposurelogViewSet(viewsets.ViewSet):
    """
    A viewset that provides
    `list`, `create`, `retrieve`, `update`, and `destroy` actions
    to be used to query the API Exposure Log Service

    Notes
    -----
    The API Exposure Log Service is a service that provides a REST API to
    query the Exposure Log database.

    The endpoint is read from the environment variable OLE_API_HOSTNAME.

    The API is documented at https://summit-lsp.lsst.codes/exposurelog/docs.
    """

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(responses={200: "Exposure logs listed"})
    def list(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/messages?{query_params_string}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={201: "Exposure log added"})
    def create(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/messages?{query_params_string}"

        # Upload files to the LFA
        lfa_urls = []
        files_to_upload = request.FILES.getlist("file[]")
        if len(files_to_upload) > 0:
            lfa_response = upload_to_lfa(request, option="upload-file")
            if lfa_response.status_code != 200:
                return lfa_response
            lfa_urls = lfa_response.data.get("urls")

        # Manage JIRA tickets
        jira_url = None
        if request.data.get("jira") == "true":
            jira_response = handle_jira_payload(request, lfa_urls=lfa_urls)
            if jira_response.status_code == 400:
                return Response(
                    jira_response.data,
                    400,
                )
            jira_url = jira_response.data.get("url")

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        if "file[]" in json_data:
            del json_data["file[]"]

        # Split lists of values separated by comma
        array_keys = {"tags"}
        for key in array_keys:
            if key in json_data:
                json_data[key] = json_data[key].split(",")

        # Add LFA and JIRA urls to the payload
        json_data["urls"] = [jira_url, *lfa_urls]
        json_data["urls"] = list(filter(None, json_data["urls"]))

        # Add user agent and user id to the payload
        json_data["user_agent"] = "LOVE"
        json_data["user_id"] = f"{request.user}@{request.get_host()}"

        # Send the request to the OLE API
        # for each obs in the obs_id list
        for obs in request.data.get("obs_id").split(","):
            json_data["obs_id"] = obs
            response = requests.post(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Exposure log retrieved"})
    def retrieve(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/messages/{pk}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Exposure log edited"})
    def update(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/messages/{pk}"

        # Upload files to the LFA
        lfa_urls = []
        files_to_upload = request.FILES.getlist("file[]")
        if len(files_to_upload) > 0:
            lfa_response = upload_to_lfa(request, option="upload-file")
            if lfa_response.status_code != 200:
                return lfa_response
            lfa_urls = lfa_response.data.get("urls")

        # Manage JIRA tickets
        jira_url = None
        if request.data.get("jira") == "true":
            jira_response = handle_jira_payload(request, lfa_urls=lfa_urls)
            if jira_response.status_code == 400:
                return Response(
                    jira_response.data,
                    400,
                )
            jira_url = jira_response.data.get("url")

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        if "file[]" in json_data:
            del json_data["file[]"]

        array_keys = {
            "tags",
            "urls",
        }
        for key in array_keys:
            if key in json_data:
                json_data[key] = json_data[key].split(",")

        # Add LFA and JIRA urls urls to the payload
        json_data["urls"] = [
            jira_url,
            *json_data.get("urls", []),
            *lfa_urls,
        ]
        json_data["urls"] = list(filter(None, json_data["urls"]))

        # Send the request to the OLE API
        response = requests.patch(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Exposure log deleted"})
    def destroy(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/messages/{pk}"
        response = requests.delete(url, json=request.data)
        if response.status_code == 204:
            return Response({"ack": "Exposure log deleted succesfully"}, status=200)
        return Response(response.json(), status=response.status_code)


class NarrativelogViewSet(viewsets.ViewSet):
    """
    A viewset that provides
    `list`, `create`, `retrieve`, `update`, and `destroy` actions
    to be used to query the API Narrative Log Service

    Notes
    -----
    The API Narrative Log Service is a service that provides a REST API to
    query the Narrative Log database.

    The endpoint is read from the environment variable OLE_API_HOSTNAME.

    The API is documented at https://summit-lsp.lsst.codes/narrativelog/docs.
    """

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(responses={200: "Narrative logs listed"})
    def list(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages?{query_params_string}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=200)

    @swagger_auto_schema(responses={201: "Narrative log added"})
    def create(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages?{query_params_string}"

        # Upload files to the LFA
        lfa_urls = []
        files_to_upload = request.FILES.getlist("file[]")
        if len(files_to_upload) > 0:
            lfa_response = upload_to_lfa(request, option="upload-file")
            if lfa_response.status_code != 200:
                return lfa_response
            lfa_urls = lfa_response.data.get("urls")

        # Manage JIRA tickets
        jira_url = None
        if request.data.get("jira") == "true":
            jira_response = handle_jira_payload(request, lfa_urls=lfa_urls)
            if jira_response.status_code == 400:
                return Response(
                    jira_response.data,
                    400,
                )
            jira_url = jira_response.data.get("url")

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        if "file[]" in json_data:
            del json_data["file[]"]

        # Split lists of values separated by comma
        array_keys = {
            "components",
            "primary_software_components",
            "primary_hardware_components",
        }
        for key in array_keys:
            if key in json_data:
                json_data[key] = json_data[key].split(",")

        # Add LFA and JIRA urls to the payload
        json_data["urls"] = [jira_url, *lfa_urls]
        json_data["urls"] = list(filter(None, json_data["urls"]))

        # Add user agent and user id to the payload
        json_data["user_agent"] = "LOVE"
        json_data["user_id"] = f"{request.user}@{request.get_host()}"

        response = requests.post(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Narrative log retrieved"})
    def retrieve(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages/{pk}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Narrative log edited"})
    def update(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages/{pk}"

        # Upload files to the LFA
        lfa_urls = []
        files_to_upload = request.FILES.getlist("file[]")
        if len(files_to_upload) > 0:
            lfa_response = upload_to_lfa(request, option="upload-file")
            if lfa_response.status_code != 200:
                return lfa_response
            lfa_urls = lfa_response.data.get("urls")

        # Manage JIRA tickets
        jira_url = None
        if request.data.get("jira") == "true":
            jira_response = handle_jira_payload(request, lfa_urls=lfa_urls)
            if jira_response.status_code == 400:
                return Response(
                    jira_response.data,
                    400,
                )
            jira_url = jira_response.data.get("url")

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        if "file[]" in json_data:
            del json_data["file[]"]

        array_keys = {
            "components",
            "primary_software_components",
            "primary_hardware_components",
            "urls",
        }
        for key in array_keys:
            if key in json_data:
                json_data[key] = json_data[key].split(",")

        # Add LFA and JIRA urls urls to the payload
        json_data["urls"] = [
            jira_url,
            *json_data.get("urls", []),
            *lfa_urls,
        ]
        json_data["urls"] = list(filter(None, json_data["urls"]))

        # Send the request to the OLE API
        response = requests.patch(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Narrative log deleted"})
    def destroy(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages/{pk}"
        response = requests.delete(url, json=request.data)
        if response.status_code == 204:
            return Response(
                {"ack": "Narrative log deleted succesfully"},
                status=200,
            )
        return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="post",
    responses={
        200: openapi.Response("Night report sent"),
        400: openapi.Response("Night report already sent"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def ole_send_night_report(request, *args, **kwargs):
    """Confirm and mark a night report as sent

    Params
    ------
    request: Request
        The Request object

    args : `list`
        List of addittional arguments. Currently unused.

    kwargs : `dict`
        Dictionary with request arguments. Currently using the following keys:
            pk (required): The primary key of the night report to be sent.

    Returns
    -------
    Response
        The response and status code of the request
        to the Open API nightreport service
    """

    pk = kwargs.get("pk", None)

    # Make a copy of the request data for payload cleaning
    # so it is json serializable
    json_data = request.data.copy()

    # Get current report
    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports/{pk}"
    response = requests.get(url, json=request.data)
    report = response.json()

    if report["date_sent"] is not None:
        return Response(
            {"error": "Night report already sent"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Trim white spaces from human written fields from the report
    for key in ["summary", "telescope_status", "confluence_url"]:
        report[key] = report[key].strip()

    # Get JIRA observation issues
    try:
        report["obs_issues"] = get_jira_obs_report({"day_obs": report["day_obs"]})
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Arrange HMTl email content
    try:
        html_content = arrange_nightreport_email(report)
        plain_content = arrange_nightreport_email(report, plain=True)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Handle email sending
    subject = f"{get_obsday_iso(report['day_obs'])} {report['telescope']} Night Log"
    email_sent = send_smtp_email(
        os.environ.get("NIGHTREPORT_MAIL_ADDRESS", "rubin-night-log@lists.lsst.org"),
        subject,
        html_content,
        plain_content,
    )
    if not email_sent:
        return Response(
            {"error": "Error sending email"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Set date_sent
    curr_tai = astropy.time.Time.now().tai.datetime
    json_data["date_sent"] = curr_tai.isoformat()

    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports/{pk}"
    response = requests.patch(url, json=json_data)

    return Response(response.json(), status=response.status_code)


class NightReportViewSet(viewsets.ViewSet):
    """
    A viewset that provides
    `list`, `create`, `retrieve`, `update`, and `destroy` actions
    to be used to query the API NightReport Log Service

    Notes
    -----
    The API NightReport Log Service is a service that provides a REST API to
    query the NightReport Log database.

    The endpoint is read from the environment variable OLE_API_HOSTNAME.

    The API is documented at https://summit-lsp.lsst.codes/nightreport/docs.
    """

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(responses={200: "NightReport logs listed"})
    def list(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports?{query_params_string}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=200)

    @swagger_auto_schema(responses={201: "NightReport log added"})
    def create(self, request, *args, **kwargs):
        query_params_string = urllib.parse.urlencode(request.query_params)
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports?{query_params_string}"

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        # Set current obs day
        curr_tai = astropy.time.Time.now().tai.datetime
        json_data["day_obs"] = int(get_obsday_from_tai(curr_tai))

        # Add user agent and user id to the payload
        json_data["user_agent"] = "LOVE"
        json_data["user_id"] = f"{request.user}@{request.get_host()}"

        response = requests.post(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "NightReport log retrieved"})
    def retrieve(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports/{pk}"
        response = requests.get(url, json=request.data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "NightReport log edited"})
    def update(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports/{pk}"

        # Make a copy of the request data for payload cleaning
        # so it is json serializable
        json_data = request.data.copy()

        # Send the request to the OLE API
        response = requests.patch(url, json=json_data)
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "NightReport log deleted"})
    def destroy(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/nightreport/reports/{pk}"
        response = requests.delete(url, json=request.data)
        if response.status_code == 204:
            return Response(
                {"ack": "NightReport log deleted succesfully"},
                status=200,
            )
        return Response(response.json(), status=response.status_code)


class ControlLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Control Locations to be viewed.

    Notes
    -----
    The API Control Location Service is a service that provides a REST API to
    query the Control Location database.
    """

    serializer_class = ControlLocationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = ControlLocation.objects.all()
        # If selected is true, filter by selected
        selected = self.request.query_params.get("selected")
        if selected is not None:
            queryset = queryset.filter(selected=True)
        return queryset


class ScriptConfigurationViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE
    instances of the ScriptConfiguration model."""

    permission_classes = (IsAuthenticated,)
    serializer_class = ScriptConfigurationSerializer

    def get_queryset(self):
        script_path = self.request.GET.get("path", "")
        script_type = self.request.GET.get("type", "")
        if script_path != "" and script_type != "":
            return (
                ScriptConfiguration.objects.filter(script_type=script_type)
                .filter(script_path=script_path)
                .order_by("-creation_timestamp")
            )
        return ScriptConfiguration.objects.order_by("-creation_timestamp")

    def create(self, request, *args, **kwargs):
        # Get the 'config_schema' and 'schema' from the request data
        config_schema = request.data.get("config_schema", "")
        get_schema = request.data.get("schema", "")

        try:
            # Parse the 'config_schema' using YAML
            config = yaml.safe_load(config_schema)
        except yaml.YAMLError as e:
            # Handle YAML parsing errors and provide detailed error information
            error = e.__dict__
            error["problem_mark"] = e.problem_mark.__dict__
            del error["context_mark"]
            return Response(
                {"title": "ERROR WHILE PARSING YAML STRING", "error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse the 'schema' using YAML
        schema = yaml.safe_load(get_schema)
        validator = DefaultingValidator(schema)

        try:
            # Validate the 'config' against the 'schema' using jsonschema
            validator.validate(config)
        except jsonschema.exceptions.ValidationError as e:
            # Handle validation errors and provide detailed error information
            error = e.__dict__
            for key in error:
                if isinstance(error[key], collections.deque):
                    error[key] = list(error[key])
            return Response(
                {
                    "title": "INVALID CONFIG YAML",
                    "error": {
                        "message": str(error["message"]),
                        "path": [] if not error["path"] else list(error["path"]),
                        "schema_path": (
                            []
                            if not error["schema_path"]
                            else list(error["schema_path"])
                        ),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use the serializer to create a new object if the data is valid
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        # Get the 'config_schema' and 'schema' from the request data
        config_schema = request.data.get("config_schema", "")
        get_schema = request.data.get("schema", "")

        try:
            # Parse the 'config_schema' using YAML
            config = yaml.safe_load(config_schema)
        except yaml.YAMLError as e:
            # Handle YAML parsing errors and provide detailed error information
            error = e.__dict__
            error["problem_mark"] = e.problem_mark.__dict__
            del error["context_mark"]
            return Response(
                {"title": "ERROR WHILE PARSING YAML STRING", "error": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse the 'schema' using YAML
        schema = yaml.safe_load(get_schema)
        validator = DefaultingValidator(schema)

        try:
            # Validate the 'config' against the 'schema' using jsonschema
            validator.validate(config)

        except jsonschema.exceptions.ValidationError as e:
            # Handle validation errors and provide detailed error information
            error = e.__dict__
            for key in error:
                if isinstance(error[key], collections.deque):
                    error[key] = list(error[key])
            return Response(
                {
                    "title": "INVALID CONFIG YAML",
                    "error": {
                        "message": str(error["message"]),
                        "path": [] if not error["path"] else list(error["path"]),
                        "schema_path": (
                            []
                            if not error["schema_path"]
                            else list(error["schema_path"])
                        ),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the instance to update
        instance = self.get_object()
        # Use the serializer to update the object if the data is valid
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
