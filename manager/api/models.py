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
Defines the Django models for this app ('api').

For more information see:
https://docs.djangoproject.com/en/2.2/topics/db/models/
"""
import json
import os

import rest_framework.authtoken.models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """Base Model for the models of this app."""

    class Meta:
        """Define attributes of the Meta class."""

        abstract = True
        """Make this an abstract class in order to be used
        as an enhanced base model"""

    creation_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Creation time"
    )
    """Creation timestamp, autogenerated upon creation"""

    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Last Updated"
    )
    """Update timestamp, autogenerated upon creation
    and autoupdated on every update"""


class Token(rest_framework.authtoken.models.Token):
    """Custome Token model with ForeignKey relation to User model.
    Based on the DRF Token model."""

    key = models.CharField(
        _("Key"), max_length=40, db_index=True, unique=True, blank=True
    )
    """ Key attribute (the token string). It is no longer primary key,
    but still indexed and unique"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_tokens",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    """ Relation to User model, it is a ForeignKey, so each user
    can have more than one token"""

    def __str__(self):
        """Define the string representation for objects of this class.

        Returns
        -------
        str
            The string representation, it is currently
            just the Token.key attribute
        """
        return self.key


class GlobalPermissions(models.Model):
    """Database-less model for custom Permissions."""

    class Meta:
        """The Meta class of this class."""

        managed = False
        """boolean: Define wether or not the model will be managed
        by the ORM (saved in the DB)"""

        permissions = (
            ("command.execute_command", "Execute Commands"),
            ("command.run_script", "Run and Requeue scripts in ScriptQueues"),
        )
        """((string, string)): Tuple defining permissions
        in the format ((<name>, <description>))"""


class ConfigFile(BaseModel):
    """ConfigFile Model, that includes actual configuration files,
    creation date and user."""

    def validate_file_extension(value):
        ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
        valid_extensions = [".json"]
        if not ext.lower() in valid_extensions:
            raise ValidationError("Unsupported file extension.")

    def validate_json_file(value):
        try:
            json.loads(value.read().decode("ascii"))
        except Exception:
            raise ValidationError("Malformatted JSON object.")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="config_files",
        on_delete=models.CASCADE,
        verbose_name="User",
    )
    """User who created the config file"""

    file_name = models.CharField(max_length=30, blank=True)
    """The custom name for the configuration"""

    config_file = models.FileField(
        max_length=200,
        upload_to="configs/",
        validators=[validate_file_extension, validate_json_file],
    )
    """Reference to the config file"""

    selected_by_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="selected_config_file",
        blank=True,
    )


class EmergencyContact(BaseModel):
    """EmergencyContact Model"""

    subsystem = models.CharField(max_length=100, blank=True)
    """EC's subsystem"""

    name = models.CharField(max_length=100, blank=True)
    """EC name"""

    contact_info = models.CharField(max_length=100, blank=True)
    """EC's preferred contact information (work number, cell, none)"""

    email = models.EmailField(max_length=254)
    """EC's email"""


class ImageTag(BaseModel):
    """ImageTag Model"""

    label = models.CharField(max_length=100, blank=True)
    key = models.CharField(max_length=50, blank=True)
    """Image label"""


class ControlLocation(BaseModel):
    """ControlLocation Model"""

    name = models.CharField(max_length=100, blank=True)
    """Control location name"""

    description = models.CharField(max_length=100, blank=True)
    """Control location description"""

    selected = models.BooleanField(default=False)
    """Control location is selected"""

    ip_whitelist = models.TextField(blank=True)
    """IP whitelist"""

    def save(self, *args, **kwargs):
        if self.selected:
            # Check if user is super user
            if not kwargs["request"].user.is_superuser:
                raise ValidationError(
                    "Only administrators can select a control location."
                )
            # Set all other instances of the model to selected=false
            ControlLocation.objects.exclude(pk=self.pk).update(selected=False)
        del kwargs["request"]
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.selected:
            raise ValidationError("Cannot delete a selected control location.")
        super().delete(*args, **kwargs)


class ScriptConfiguration(models.Model):
    """ScriptConfiguration model, includes all the fields"""

    class ScriptTypes(models.TextChoices):
        STANDARD = "standard", "standard"
        EXTERNAL = "external", "external"

    script_path = models.CharField(max_length=100)
    """The path of the script. It will be saved in this format:
    auxtel/calsys_take.py"""
    config_name = models.CharField(max_length=50)
    """The name that will have the saved custom configuration"""
    config_schema = models.TextField()
    """The config schema that will be saved """
    script_type = models.CharField(
        max_length=10, choices=ScriptTypes.choices, default=None
    )
    """The type of the script, it's referenced as 'standard' or 'external'  """
    creation_timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    """The creation timestamp.
    This timestamp will generate automatically once the script is saved
    """

    def __str__(self) -> str:
        """Define the string representation for objects of this class.

        Returns
        -------
        str
            The string representation as:
            f"[self.id] {self.script_type} - "
            f"{self.script_path}[{self.config_name}]"
        """
        return (
            f"[{self.id}] {self.script_type} - {self.script_path} - {self.config_name}"
        )
