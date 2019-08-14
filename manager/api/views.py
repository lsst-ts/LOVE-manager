"""Defines the views exposed by the REST API exposed by this app ('api')."""
from rest_framework import status
# from rest_framework.authtoken.models import Token
from api.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.serializers import UserSerializer


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
    user = request.user
    user_data = UserSerializer(user).data
    return Response(
        {
            'detail': 'Token is valid',
            'user_data': user_data,
            'permissions': {
                'execute_commands': user.has_perm('api.command.execute_command')
            },
        },
        status=status.HTTP_200_OK
    )


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
        user_data = UserSerializer(user).data
        return Response({
            'token': token.key,
            'user_data': user_data,
            'permissions': {
                'execute_commands': user.has_perm('api.command.execute_command')
            },
        })
