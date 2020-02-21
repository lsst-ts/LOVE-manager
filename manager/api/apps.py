"""Django apps configuration for the api app."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """General App config class. Currently defines the name of the app."""

    name = 'api'

    def ready(self):
        """Import the signals module when the application is ready."""
        import api.signals
