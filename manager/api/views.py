from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.serializers import UserSerializer


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def validate_token(request):
    """ Validates the token and returns 200 code if valid """
    return Response({'detail': 'Token is valid'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def logout(request):
    """ Logouts and deletes the token. And returns 204 code if valid """
    token = request._auth
    token.delete()
    return Response({'detail': 'Logout successful, Token succesfully deleted'}, status=status.HTTP_204_NO_CONTENT)


class CustomObtainAuthToken(ObtainAuthToken):
    """ API endpoint to obtain authorization tokens """

    def post(self, request, *args, **kwargs):
        """ Handle post requests """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.create(user=user)
        user_data = UserSerializer(user).data

        return Response({
            'token': token.key,
            'user_data': user_data,
        })
