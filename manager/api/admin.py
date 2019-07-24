"""
Defines the Django Admin model pages for this app ('api').

Registers the models that will be available throgh the Djangpo Admin interface.

For more information see:
https://docs.djangoproject.com/en/2.1/ref/contrib/admin/
"""
from django.contrib import admin
from api.models import Token


admin.site.register(Token)
