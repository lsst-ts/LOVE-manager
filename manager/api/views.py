"""Defines the views exposed by the REST API exposed by this app."""
import os
import requests
import yaml
import jsonschema
import collections
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.models import Token
from api.serializers import TokenSerializer
from .schema_validator import DefaultingValidator
valid_response = openapi.Response('Valid token', TokenSerializer)
invalid_response = openapi.Response('Invalid token')


@swagger_auto_schema(method='get', responses={200: valid_response, 401: invalid_response})
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def validate_token(request):
    """Validate the token and return 200 code if valid.

    If the token is invalid this function is not executed (the request fails before)

    Returns
    -------
    Response
        The response stating that the token is valid with a 200 status code.
    """
    token_key = request.META.get('HTTP_AUTHORIZATION')[6:]
    token = Token.objects.get(key=token_key)
    return Response(TokenSerializer(token).data)


@swagger_auto_schema(method='delete', responses={204: openapi.Response('Logout Successful')})
@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def logout(request):
    """Logout and delete the token. And returns 204 code if valid.

    If the token is invalid this function is not executed (the request fails before)

    Returns
    -------
    Response
        The response stating that the token has been deleted, with a 204 status code.
    """
    token = request._auth
    token.delete()
    return Response({'detail': 'Logout successful, Token succesfully deleted'}, status=status.HTTP_204_NO_CONTENT)


class CustomObtainAuthToken(ObtainAuthToken):
    """API endpoint to obtain authorization tokens."""

    login_response = openapi.Response('Login succesful', TokenSerializer)
    login_failed_response = openapi.Response('Login failed')

    @swagger_auto_schema(responses={200: login_response, 400: login_failed_response})
    def post(self, request, *args, **kwargs):
        """Handle the (post) request for token.

        If the token is invalid this function is not executed (the request fails before)

        Params
        ------
        request: Request
            The Requets object
        args: list
            List of addittional arguments. Currenlty unused
        kwargs: dict
            Dictionary with addittional keyword arguments (indexed by keys in the dict). Currenlty unused

        Returns
        -------
        Response
            The response containing the token and other user data.
        """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.create(user=user)
        return Response(TokenSerializer(token).data)


@swagger_auto_schema(method='post', responses={200: valid_response, 401: invalid_response})
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def validate_config_schema(request):
    """Validate a configuration yaml with using a schema

    Returns
    -------
    Response
        Dictionary containing a 'title' and an 'error' key (if any)
        or an 'output' with the output of the validator (config with defaults-autocomplete)
    """
    try:
        config = yaml.safe_load(request.data['config'])
    except yaml.YAMLError as e:
        error = e.__dict__
        error['problem_mark'] = e.problem_mark.__dict__
        del error['context_mark']
        return Response({
            'title': 'ERROR WHILE PARSING YAML STRING',
            'error': error
        })
    schema = yaml.safe_load(request.data['schema'])
    validator = DefaultingValidator(schema)

    try:
        output = validator.validate(config)
        return Response({'title': 'None', "output": output})
    except jsonschema.exceptions.ValidationError as e:
        error = e.__dict__
        for key in error:
            if(type(error[key]) == collections.deque):
                error[key] = list(error[key])

        return Response({
            'title': 'INVALID CONFIG YAML',
            'error': {
                'message': str(error["message"]),
                "path": [] if not error['path'] else list(error['path']),
                "schema_path": [] if not error['schema_path'] else list(error['schema_path']),
            }
        })


@swagger_auto_schema(method='post', responses={200: valid_response, 401: invalid_response})
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def commander(request):
    """Sends a command to the LOVE-commander according to the received parameters
    """
    url = f"http://{os.environ.get('COMMANDER_HOSTNAME')}:{os.environ.get('COMMANDER_PORT')}/cmd"
    response = requests.post(url, json=request.data)
    return Response(response.json(), status=response.status_code)
