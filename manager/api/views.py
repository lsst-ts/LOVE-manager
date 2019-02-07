from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def validate_token(request):
    return Response({'detail': 'Token is valid'}, status=status.HTTP_200_OK)
