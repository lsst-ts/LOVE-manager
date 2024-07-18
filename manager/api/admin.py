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


"""
Defines the Django Admin model pages for this app .

Registers the models that will be available throgh the Djangpo Admin interface.

For more information see:
https://docs.djangoproject.com/en/2.2/ref/contrib/admin/
"""
from api.models import (
    ConfigFile,
    ControlLocation,
    EmergencyContact,
    ImageTag,
    ScriptConfiguration,
    Token,
    ZephyrScaleCredential,
)
from django import forms
from django.contrib import admin

# from django.contrib.auth.models import Permission


class ControlLocationAdmin(admin.ModelAdmin):
    """Customize the ControlLocation admin page."""

    def save_model(self, request, obj, form, change):
        """Override the save_model method to pass the request argument."""
        obj.save(request=request)


class ZephyrScaleCredentialForm(forms.ModelForm):
    """Customize the ZephyrScaleCredential form."""

    class Meta:
        """Define the attributes of the Meta class."""

        model = ZephyrScaleCredential
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Override the __init__ method to pass the request"""
        super(ZephyrScaleCredentialForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["jira_api_token"].widget = forms.PasswordInput(
                render_value=True
            )
            self.fields["zephyr_api_token"].widget = forms.PasswordInput(
                render_value=True
            )


class ZephyrScaleCredentialAdmin(admin.ModelAdmin):
    """Customize the ZephyrScaleCredential admin page."""

    form = ZephyrScaleCredentialForm


admin.site.register(Token)
admin.site.register(ConfigFile)
admin.site.register(EmergencyContact)
admin.site.register(ImageTag)
admin.site.register(ControlLocation, ControlLocationAdmin)
admin.site.register(ScriptConfiguration)
admin.site.register(ZephyrScaleCredential, ZephyrScaleCredentialAdmin)
# admin.site.register(Permission)
