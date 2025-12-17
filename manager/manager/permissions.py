from api.models import ControlLocation
from django.conf import settings
from rest_framework.permissions import BasePermission

from manager.utils import get_client_ip


class LocationPermission(BasePermission):
    """Permission class to check if the user is in the location whitelist."""

    message = {"ack": "Your location is not allowed to command the observatory."}

    def has_permission(self, request, view):
        """Return True if the request comes from a location
        configured as command location."""

        selected_location = ControlLocation.objects.filter(selected=True).first()
        location = selected_location if selected_location else ControlLocation.objects.first()
        client_ip = get_client_ip(request)
        return client_ip in location.ip_whitelist


class UserBasedPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    message = {"ack": "Your user is not allowed to command the observatory."}

    def has_permission(self, request, view):
        """Return True if the user has command permissions."""
        return request.user.has_perm("api.command.execute_command")


class CommandPermission(BasePermission):
    """Permission class to check if the user has commanding permissions."""

    def __new__(cls) -> BasePermission:
        """Return the correct permission class based on
        the configured permission type."""
        configured_command_permission = settings.COMMANDING_PERMISSION_TYPE
        if configured_command_permission == "user":
            return UserBasedPermission()
        elif configured_command_permission == "location":
            return LocationPermission()
        else:
            raise ValueError(f"Invalid permission type: {configured_command_permission}")
