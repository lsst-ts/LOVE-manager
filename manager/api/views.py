"""Defines the views exposed by the REST API exposed by this app."""
import os
import json
import requests
import yaml
import jsonschema
import collections
from background_task import background
import urllib
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models.query_utils import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import viewsets, status, mixins
from api.models import (
    Token,
    ConfigFile,
    EmergencyContact,
    ImageTag,
    CSCAuthorizationRequest,
)
from api.serializers import TokenSerializer, ConfigSerializer
from api.serializers import (
    ConfigFileSerializer,
    ConfigFileContentSerializer,
    EmergencyContactSerializer,
    ImageTagSerializer,
    CSCAuthorizationRequestSerializer,
    CSCAuthorizationRequestCreateSerializer,
    CSCAuthorizationRequestUpdateSerializer,
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

    If the token is invalid this function is not executed (the request fails before)


    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currenlty unused
    kwargs: dict
        Dictionary with addittional keyword arguments (indexed by keys in the dict),
        one optional parameter that could be expeted is `flags`

    Returns
    -------
    Response
        The response stating that the token is valid with a 200 status code.
    """
    flags = kwargs.get("flags", None)
    no_config = flags == "no_config" or flags == "no-config"
    token_key = request.META.get("HTTP_AUTHORIZATION")[6:]
    token = Token.objects.get(key=token_key)
    data = TokenSerializer(token, context={"no_config": no_config}).data
    return Response(data)


@swagger_auto_schema(
    method="delete", responses={204: openapi.Response("Logout Successful")}
)
@api_view(["DELETE"])
@permission_classes((IsAuthenticated,))
def logout(request):
    """Logout and delete the token. And returns 204 code if valid.

    If the token is invalid this function is not executed (the request fails before)

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response stating that the token has been deleted, with a 204 status code.
    """
    token = request._auth
    token.delete()
    return Response(
        {"detail": "Logout successful, Token succesfully deleted"},
        status=status.HTTP_204_NO_CONTENT,
    )


class CustomObtainAuthToken(ObtainAuthToken):
    """API endpoint to obtain authorization tokens."""

    login_response = openapi.Response("Login succesful", TokenSerializer)
    login_failed_response = openapi.Response("Login failed")

    @swagger_auto_schema(responses={200: login_response, 400: login_failed_response})
    def post(self, request, *args, **kwargs):
        """Handle the (post) request for token.

        If the token is invalid this function is not executed (the request fails before)

        Params
        ------
        request: Request
            The Request object
        args: list
            List of addittional arguments. Currenlty unused
        kwargs: dict
            Dictionary with addittional keyword arguments (indexed by keys in the dict). Currenlty unused

        Returns
        -------
        Response
            The response containing the token and other user data.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = Token.objects.create(user=user)
        return Response(TokenSerializer(token).data)


class CustomSwapAuthToken(ObtainAuthToken):
    """API endpoint to obtain authorization tokens."""

    login_response = openapi.Response("User swap succesful", TokenSerializer)
    login_failed_response = openapi.Response("User swap failed")

    @swagger_auto_schema(responses={200: login_response, 400: login_failed_response})
    @permission_classes((IsAuthenticated,))
    def post(self, request, *args, **kwargs):
        """Handle the (post) request for token.

        If the token is invalid this function is not executed (the request fails before)

        Params
        ------
        request: Request
            The Request object
        args: list
            List of addittional arguments. Currently unused
        kwargs: dict
            Dictionary with addittional keyword arguments (indexed by keys in the dict). Currenlty unused

        Returns
        -------
        Response
            The response containing the token and other user data.
        """
        if not request.user.is_authenticated or not request._auth:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = Token.objects.create(user=user)
        old_token = request._auth
        old_token.delete()

        flags = kwargs.get("flags", None)
        no_config = flags == "no_config" or flags == "no-config"
        data = TokenSerializer(token, context={"no_config": no_config}).data
        return Response(data)


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
        or an 'output' with the output of the validator (config with defaults-autocomplete)
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
            if type(error[key]) == collections.deque:
                error[key] = list(error[key])

        return Response(
            {
                "title": "INVALID CONFIG YAML",
                "error": {
                    "message": str(error["message"]),
                    "path": [] if not error["path"] else list(error["path"]),
                    "schema_path": []
                    if not error["schema_path"]
                    else list(error["schema_path"]),
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
@permission_classes((IsAuthenticated,))
def commander(request):
    """Sends a command to the LOVE-commander according to the received parameters

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    if not request.user.has_perm("api.command.execute_command"):
        return Response(
            {"ack": "User does not have permissions to execute commands."}, 401
        )
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
@permission_classes((IsAuthenticated,))
def lovecsc_observinglog(request):
    """Sends an observing log message to the LOVE-commander according to the received parameters

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    if not request.user.has_perm("api.command.execute_command"):
        return Response(
            {"ack": "User does not have permissions to send observing logs."}, 401
        )
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lovecsc/observinglog"
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
    of <csc name>: { "command_names": [], "event_names": [], "telemetry_names": []}

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
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/salinfo/topic-names{query}"
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
     of <csc name>: { "command_data": [], "event_data": [], "telemetry_data": []}

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
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/salinfo/topic-data{query}"
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
    """Adds the current User to the selected_by_users of the specified Config file

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

        serializer = ConfigFileContentSerializer(cf)
        return Response(serializer.data)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the EmergencyContact model."""

    queryset = EmergencyContact.objects.order_by("subsystem").all()
    """Set of objects to be accessed by queries to this viewsets endpoints"""

    serializer_class = EmergencyContactSerializer
    """Serializer used to serialize View objects"""


class ImageTagViewSet(viewsets.ModelViewSet):
    """GET, POST, PUT, PATCH or DELETE instances the EmergencyContact model."""

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
    """Queries data from an EFD timeseries by redirecting the request to the Commander

    Params
    ------
    request: Request
        The Request object
        Dictionary with request arguments. Request should contain the following:
            start_date (required): String specifying the start of the query range. Default current date minus 10 minutes
            timewindow (required): Int specifying the number of minutes to query starting from start_date. Default 10
            topics (required): Dictionary of the form
                {
                    CSC1: {
                        index: [topic1, topic2...],
                    },
                    CSC2: {
                        index: [topic1, topic2...],
                    },
                }
            resample (optional): The offset string representing target resample conversion, e.g. '15min', '10S'
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
    """Queries data from an EFD timeseries by redirecting the request to the Commander

    Params
    ------
    request: Request
        The Request object
        Dictionary with request arguments. Request should contain the following:
            start_date (required): String specifying the start of the query range.
            end_date (required): String specifying the end of the query range.
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
def tcs_aux_command(request, *args, **kwargs):
    """Sends command to the ATCS

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments. Request should contain the following:
            command_name (required): The name of the command to be run.
            It should be a field of the lsst.ts.observatory.control.auxtel.ATCS class
            params (required): Parameters to be passed to the command method, e.g.
                {
                    ra: 80,
                    dec: 30,
                }

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    if not request.user.has_perm("api.command.execute_command"):
        return Response(
            {"ack": "User does not have permissions to execute commands."}, 401
        )
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
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/tcs/aux/docstrings"
    response = requests.get(url)
    return Response(response.json(), status=response.status_code)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def tcs_main_command(request, *args, **kwargs):
    """Sends command to the MTCS

    Params
    ------
    request: Request
        The Request object
    args: list
        List of addittional arguments. Currently unused
    kwargs: dict
        Dictionary with request arguments. Request should contain the following:
            command_name (required): The name of the command to be run. It should be a field of the
            lsst.ts.observatory.control.maintel.MTCS class
            params (required): Parameters to be passed to the command method, e.g.
                {
                    ra: 80,
                    dec: 30,
                }

    Returns
    -------
    Response
        The response and status code of the request to the LOVE-Commander
    """
    if not request.user.has_perm("api.command.execute_command"):
        return Response(
            {"ack": "User does not have permissions to execute commands."}, 401
        )
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
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/tcs/main/docstrings"
    response = requests.get(url)
    return Response(response.json(), status=response.status_code)


# @api_view(["POST"])
# @permission_classes((IsAuthenticated,))
def lfa(request, *args, **kwargs):
    """Connects to LFA API to upload a new file

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
        The response and status code of the request to the LOVE-commander LFA API
    """

    option = kwargs.get("option", None)
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/lfa/{option}"

    uploaded_files_urls = []
    for file in request.FILES:
        upload_file_response = requests.post(
            url, files={"uploaded_file": request.FILES[file]}
        )
        if upload_file_response.status_code == 200:
            uploaded_files_urls.append(upload_file_response.json().get("url"))
        elif upload_file_response.status_code == 404:
            return Response({"ack": "Option not available"}, status=400)
        else:
            return Response(
                upload_file_response.json(), status=upload_file_response.status_code
            )

    return Response(
        {"ack": "All files uploaded correctly", "urls": uploaded_files_urls}, status=200
    )


class CSCAuthorizationRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.

    """

    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CSCAuthorizationRequestCreateSerializer
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return CSCAuthorizationRequestUpdateSerializer
        return CSCAuthorizationRequestSerializer

    def get_queryset(self):
        if self.request.user.has_perm("api.authlist.administrator"):
            return CSCAuthorizationRequest.objects.all()
        else:
            return CSCAuthorizationRequest.objects.filter(
                Q(user__username=self.request.user.username)
                | Q(authorized_users__icontains=self.request.user.username)
            )

    @swagger_auto_schema(responses={201: CSCAuthorizationRequestSerializer(many=True)})
    def create(self, request, *args, **kwargs):
        created_authorizations = []
        authorization_obj = CSCAuthorizationRequest(*args, **kwargs)
        authorization_obj.user = request.user
        authorization_obj.cscs_to_change = request.data.get("cscs_to_change")
        authorization_obj.authorized_users = request.data.get("authorized_users")
        authorization_obj.unauthorized_cscs = request.data.get("unauthorized_cscs")
        authorization_obj.requested_by = request.data.get("requested_by")
        request_duration = request.data.get("duration")
        authorization_obj.duration = (
            request_duration
            if request_duration != "" and request_duration != 0
            else None
        )
        request_message = request.data.get("message")
        authorization_obj.message = request_message if request_message != "" else None

        if request.user.has_perm("api.authlist.administrator"):
            authorization_obj.status = "Authorized"
            authorization_obj.resolved_by = request.user
            authorization_obj.resolved_at = timezone.now()

        authorization_self_remove_obj = None
        if f"-{authorization_obj.requested_by}" in authorization_obj.authorized_users:
            authorization_self_remove_obj = CSCAuthorizationRequest(*args, **kwargs)
            authorization_self_remove_obj.user = request.user
            authorization_self_remove_obj.cscs_to_change = request.data.get(
                "cscs_to_change"
            )
            authorization_self_remove_obj.authorized_users = (
                f"-{authorization_obj.requested_by}"
            )
            authorization_self_remove_obj.unauthorized_cscs = ""
            authorization_self_remove_obj.requested_by = request.data.get(
                "requested_by"
            )
            authorization_self_remove_obj.status = "Authorized"
            authorization_self_remove_obj.message = "User self removed authorization."
            authorization_self_remove_obj.resolved_by = request.user
            authorization_self_remove_obj.resolved_at = timezone.now()
            authorization_self_remove_obj.save()
            query_authorize_csc(
                CSCAuthorizationRequestSerializer(authorization_self_remove_obj).data
            )
            created_authorizations.append(authorization_self_remove_obj)

            new_authorized_users = request.data.get("authorized_users").split(",")
            new_authorized_users.remove(f"-{authorization_obj.requested_by}")
            authorization_obj.authorized_users = ",".join(new_authorized_users)

        if (
            authorization_obj.authorized_users != ""
            or authorization_obj.unauthorized_cscs != ""
        ):
            authorization_obj.save()
            created_authorizations.append(authorization_obj)

            if authorization_obj.status == "Authorized":
                query_authorize_csc(
                    CSCAuthorizationRequestSerializer(authorization_obj).data
                )

                if authorization_obj.duration and int(authorization_obj.duration) > 0:
                    authlist_revert_authorization_task(
                        CSCAuthorizationRequestSerializer(authorization_obj).data,
                        schedule=(int(authorization_obj.duration) * 60) - 5,
                    )

        if len(created_authorizations) > 0:
            return Response(
                CSCAuthorizationRequestSerializer(
                    created_authorizations, many=True
                ).data,
                status=201,
            )
        else:
            return Response(
                {"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(responses={200: CSCAuthorizationRequestSerializer()})
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == CSCAuthorizationRequest.RequestStatus.PENDING:
            if not request.user.has_perm("api.authlist.administrator"):
                raise PermissionDenied()
            updated_instance = self.get_object()
            updated_instance.status = request.data.get("status")
            updated_instance.duration = request.data.get("duration")
            updated_instance.message = request.data.get("message")
            updated_instance.resolved_by = request.user
            updated_instance.resolved_at = timezone.now()
            updated_instance.save()
            query_authorize_csc(
                CSCAuthorizationRequestSerializer(updated_instance).data
            )

            if updated_instance.duration and int(updated_instance.duration) > 0:
                authlist_revert_authorization_task(
                    CSCAuthorizationRequestSerializer(updated_instance).data,
                    schedule=(int(updated_instance.duration) * 60) - 5,
                )

            return Response(
                CSCAuthorizationRequestSerializer(updated_instance).data, status=200
            )
        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)


def query_authorize_csc(authorization_dict):
    cmd_payload = {
        "csc": "Authorize",
        "salindex": 0,
        "cmd": "cmd_requestAuthorization",
        "params": {
            "cscsToChange": authorization_dict["cscs_to_change"],
            "authorizedUsers": authorization_dict["authorized_users"],
            "nonAuthorizedCSCs": authorization_dict["unauthorized_cscs"],
        },
    }

    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/cmd"
    response = requests.post(url, json=cmd_payload)
    return Response(response.json(), status=response.status_code)


@background(schedule=60)
def authlist_revert_authorization_task(authorization_dict):
    new_authorized_users = (
        authorization_dict["authorized_users"]
        .replace("+", "[plus]")
        .replace("-", "[minus]")
        .replace("[plus]", "-")
        .replace("[minus]", "+")
    )
    new_unauthorized_cscs = (
        authorization_dict["unauthorized_cscs"]
        .replace("+", "[plus]")
        .replace("-", "[minus]")
        .replace("[plus]", "-")
        .replace("[minus]", "+")
    )
    authorization_dict["authorized_users"] = new_authorized_users
    authorization_dict["unauthorized_cscs"] = new_unauthorized_cscs
    query_authorize_csc(authorization_dict)


def getTitle(request_data):
    # Shared params
    request_type = request_data["request_type"]

    # Exposure log params
    if request_type == "exposure":
        try:
            obs_id = request_data["obs_id"]
            return "LOVE generated: " + request_type + " | " + obs_id
        except Exception:
            raise Exception("Error reading params")
    # Narrative log params
    if request_type == "narrative":
        try:
            system = request_data["system"]
            return "LOVE generated: " + request_type + " | " + system
        except Exception:
            raise Exception("Error reading params")
    return ""


def makeJiraDescription(request_data):
    # Shared params
    request_type = request_data["request_type"]
    try:
        lfa_files_urls = request_data["lfa_files_urls"]
        message_log = request_data["message_text"]
        user_id = request_data["user_id"]
        user_agent = request_data["user_agent"]
    except Exception:
        raise Exception("Error reading params")

    # Exposure log params
    if request_type == "exposure":
        try:
            obs_id = request_data["obs_id"]
            instrument = request_data["instrument"]
            exposure_flag = request_data["exposure_flag"]
        except Exception:
            raise Exception("Error reading params")
        description = (
            "*Created by* "
            + user_id
            + " *from* "
            + user_agent
            + "\n"
            + "*Observation id:* "
            + obs_id
            + "\n"
            + "*Instrument:* "
            + instrument
            + "\n"
            + "*Exposure flag:* "
            + exposure_flag
            + "\n"
            + "*Files:* "
            + "\n"
            + str(lfa_files_urls)
            + "\n\n"
            + message_log
        )
    # Narrative log params
    if request_type == "narrative":
        try:
            system = request_data["system"]
            subsystems = request_data["subsystems"]
            cscs = request_data["cscs"]
            begin_date = request_data["begin_date"]
            end_date = request_data["end_date"]
            time_lost = str(request_data["time_lost"])
        except Exception:
            raise Exception("Error reading params")
        description = (
            "*Created by* "
            + user_id
            + " *from* "
            + user_agent
            + "\n"
            + "*Time of incident:* "
            + begin_date
            + " *-* "
            + end_date
            + "\n"
            + "*Time lost:* "
            + time_lost
            + "\n"
            + "*System:* "
            + system
            + "\n"
            + "*Subsystems:* "
            + "\n"
            + str(subsystems)
            + "\n"
            + "*CSCs:* "
            + "\n"
            + str(cscs)
            + "\n"
            + "*Files:* "
            + "\n"
            + str(lfa_files_urls)
            + "\n\n"
            + message_log
        )

    return description if description is not None else ""


def jira(request):
    """Connects to JIRA API to create a ticket on a specific project.
    For more information on issuetypes refer to:
    ttps://jira.lsstcorp.org/rest/api/latest/issuetype/?projectId=JIRA_PROJECT_ID

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API
    """
    if not request.user.has_perm("api.command.execute_command"):
        return Response(
            {"ack": "User does not have permissions to execute commands."}, 403
        )

    m_request = {
        "request_type": "non-exposure",  # exposure
        "type_comment": "test",
        "obs_time_loss": 10,
        "salindex": 1,
        "subsystem": "MainTel",
        "csc": "M1M3",
        "csc_parameter": "actual",
        "time_of_incedent": "00:35:00",
        "exposure_flag": None,
        "obs_id": None,
        "lfa_file_url": "asdf.com",
        "message": """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Donec sagittis aliquam lacus et euismod. Nullam tortor metus,
            mollis faucibus mauris convallis, mattis commodo magna. Sed blandit
            dapibus lectus et sollicitudin. Aliquam erat lorem, posuere
            at fermentum quis, finibus sed nunc. Nulla facilisi.
            Maecenas vitae dignissim quam.""",
    }

    jira_payload = {
        "fields": {"project": {"id": 13700}},
        "labels": ["LOVE", m_request["request_type"]],
        "summary": getTitle(m_request),
        "description": makeJiraDescription(m_request),
    }
    print("+++++++++++", flush=True)
    print(jira_payload, flush=True)
    print("+++++++++++", flush=True)
    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }

    # TODO: get JIRA authorization (login)
    # url = f"http://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/issue/"
    # lfa_file_url = "asd"
    url = f"https://jsonplaceholder.typicode.com/posts/"
    # response = requests.post(url, json=jira_payload, headers=headers)
    response = requests.get(url, json=jira_payload, headers=headers)
    print("#############", flush=True)
    print(response.json(), flush=True)
    print("#############", flush=True)

    return Response(response.json(), status=response.status_code)


@swagger_auto_schema(
    method="post",
    responses={
        200: openapi.Response("LFA file uploaded"),
        401: openapi.Response("Unauthenticated"),
        403: openapi.Response("Unauthorized"),
    },
)
@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def lfa(request):
    """Connects to LFA API to upload a new file

    Params
    ------
    request: Request
        The Request object

    Returns
    -------
    Response
        The response and status code of the request to the JIRA API
    """
    full_request = request.data

    if "request_type" not in full_request:
        return Response({"ack": "Error reading request type"}, status=400)

    try:
        jira_payload = {
            "fields": {
                "project": {"id": os.environ.get("JIRA_PROJECT_ID")},
                "labels": [
                    "LOVE",
                    # full_request["request_type"],
                    *full_request["tags"].split(","),
                ],
                "summary": getTitle(full_request),
                "description": makeJiraDescription(full_request),
                "issuetype": {"id": 12601},
            },
            "update": {"components": [{"set": [{"name": "Dev"}]}],},
        }
    except Exception:
        return Response({"ack": "Error creating jira payload"}, status=400)

    headers = {
        "Authorization": f"Basic {os.environ.get('JIRA_API_TOKEN')}",
        "content-type": "application/json",
    }
    url = f"https://{os.environ.get('JIRA_API_HOSTNAME')}/rest/api/latest/issue/"
    response = requests.post(url, json=jira_payload, headers=headers)
    response_data = response.json()
    return Response(
        {
            "ack": "Jira ticket created",
            "url": f"https://jira.lsstcorp.org/browse/{response_data['key']}",
        },
        status=200,
    )


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
        The response and status code of the request to the Open API exposurelog service
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
        The response and status code of the request to the Open API exposurelog service
    """

    query_params_string = urllib.parse.urlencode(request.query_params)
    url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/exposurelog/instruments?{query_params_string}"
    response = requests.get(url, json=request.data)

    return Response(response.json(), status=response.status_code)


class ExposurelogViewSet(viewsets.ViewSet):
    """
    A viewset that provides `list`, `create`, `retrieve`, `update`, and `destroy` actions
    to be used to query the Open API Exposure Log Service

    """

    # serializer_class = ExposureLogSerializer
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

        lfa_urls = []
        if "file" in request.data:
            lfa_response = lfa(request, option="upload-file")
            if lfa_response.status_code == 400 or lfa_response.status_code == 404:
                return Response(lfa_response.json(), lfa_response.status_code)
            lfa_urls = lfa_response.data.get("urls")

        jira_url = None
        if request.data.get("jira") == "true":
            request.data._mutable = True
            request.data["user_agent"] = "LOVE"
            request.data["user_id"] = f"{request.user}@{request.get_host()}"
            request.data["lfa_files_urls"] = lfa_urls
            request.data._mutable = False
            jira_response = jira(request)
            if jira_response.status_code == 400:
                return Response(
                    {"ack": "Jira ticket could not be created"},
                    jira_response.status_code,
                )
            jira_url = jira_response.data.get("url")

        json_data = request.data.copy()
        if "file" in json_data:
            del json_data["file"]

        if "tags" in json_data:
            json_data["tags"] = json_data["tags"].split(",")
        if "systems" in json_data:
            json_data["systems"] = json_data["systems"].split(",")
        if "subsystems" in json_data:
            json_data["subsystems"] = json_data["subsystems"].split(",")
        if "cscs" in json_data:
            json_data["cscs"] = json_data["cscs"].split(",")

        json_data["urls"] = [jira_url, *lfa_urls]
        json_data["urls"] = list(filter(None, json_data["urls"]))

        json_data["user_agent"] = "LOVE"
        json_data["user_id"] = f"{request.user}@{request.get_host()}"

        # for obs in request.data.get('obs_ids', []):
        #     response = requests.post(url, json=json_data)
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

        json_data = request.data.copy()
        if "tags" in json_data:
            json_data["tags"] = json_data["tags"].split(",")
        if "systems" in json_data:
            json_data["systems"] = json_data["systems"].split(",")
        if "subsystems" in json_data:
            json_data["subsystems"] = json_data["subsystems"].split(",")
        if "cscs" in json_data:
            json_data["cscs"] = json_data["cscs"].split(",")

        if "urls" in json_data:
            json_data["urls"] = json_data["urls"].split(",")

        response = requests.patch(url, json=json_data)
        # TODO: allow uploading a file on update
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
    A viewset that provides `list`, `create`, `retrieve`, `update`, and `destroy` actions
    to be used to query the Open API Narrative Log Service

    """

    # serializer_class = NarrativeLogSerializer
    permission_classes = (IsAuthenticated,)

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

        lfa_urls = []
        if "file" in request.data:
            lfa_response = lfa(request, option="upload-file")
            if lfa_response.status_code == 400 or lfa_response.status_code == 404:
                return Response(lfa_response.json(), lfa_response.status_code)
            lfa_urls = lfa_response.data.get("urls")

        jira_url = None
        if request.data.get("jira") == "true":
            request.data._mutable = True
            request.data["lfa_files_urls"] = lfa_urls
            request.data["user_agent"] = "LOVE"
            request.data["user_id"] = f"{request.user}@{request.get_host()}"
            request.data._mutable = False
            jira_response = jira(request)
            if jira_response.status_code == 400:
                return Response(
                    {"ack": "Jira ticket could not be created"},
                    jira_response.status_code,
                )
            jira_url = jira_response.data.get("url")

        json_data = request.data.copy()
        if "file" in json_data:
            del json_data["file"]

        if "tags" in json_data:
            json_data["tags"] = json_data["tags"].split(",")

        json_data["urls"] = [jira_url, *lfa_urls]
        json_data["urls"] = list(filter(None, json_data["urls"]))

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

        json_data = request.data.copy()
        if "tags" in json_data:
            json_data["tags"] = json_data["tags"].split(",")

        if "urls" in json_data:
            json_data["urls"] = json_data["urls"].split(",")

        response = requests.patch(url, json=json_data)
        # TODO: allow uploading a file on update
        return Response(response.json(), status=response.status_code)

    @swagger_auto_schema(responses={200: "Narrative log deleted"})
    def destroy(self, request, pk=None, *args, **kwargs):
        url = f"http://{os.environ.get('OLE_API_HOSTNAME')}/narrativelog/messages/{pk}"
        response = requests.delete(url, json=request.data)
        if response.status_code == 204:
            return Response({"ack": "Narrative log deleted succesfully"}, status=200,)
        return Response(response.json(), status=response.status_code)
