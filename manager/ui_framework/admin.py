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
from django.contrib import admin
from .models import Workspace, View, WorkspaceView

admin.site.register(Workspace)
admin.site.register(View)
admin.site.register(WorkspaceView)
