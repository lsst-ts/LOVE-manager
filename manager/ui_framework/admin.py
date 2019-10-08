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
