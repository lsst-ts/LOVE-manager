"""
Defines the Django Admin model pages for this app .

Registers the models that will be available throgh the Djangpo Admin interface.

For more information see:
https://docs.djangoproject.com/en/2.2/ref/contrib/admin/
"""
from django.contrib import admin
from api.models import (
    Token,
    ConfigFile,
    EmergencyContact,
    ImageTag,
    CSCAuthorizationRequest,
    ControlLocation,
    ScriptConfiguration,
)

# from django.contrib.auth.models import Permission


class ControlLocationAdmin(admin.ModelAdmin):
    """Customize the ControlLocation admin page."""

    def save_model(self, request, obj, form, change):
        """Override the save_model method to pass the request argument."""
        obj.save(request=request)


admin.site.register(Token)
admin.site.register(ConfigFile)
admin.site.register(EmergencyContact)
admin.site.register(ImageTag)
admin.site.register(CSCAuthorizationRequest)
admin.site.register(ControlLocation, ControlLocationAdmin)
admin.site.register(ScriptConfiguration)
# admin.site.register(Permission)
