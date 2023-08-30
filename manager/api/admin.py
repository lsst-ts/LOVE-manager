# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile and Vera C. Rubin Observatory Telescope
# and Site Systems.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


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
