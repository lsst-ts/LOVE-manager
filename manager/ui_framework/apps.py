"""Django apps configuration for the ui_framework app."""
from django.apps import AppConfig


class UiFrameworkConfig(AppConfig):
    """General App config class. Currently defines the name of the app."""

    name = "ui_framework"
    """The name of the app."""

    def ready(self):
        """ Import signals module when app is ready """
        import ui_framework.signals
