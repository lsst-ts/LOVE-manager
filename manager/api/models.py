"""
Defines the Django models for this app ('api').

For more information see:
https://docs.djangoproject.com/en/2.1/topics/db/models/
"""
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
import rest_framework.authtoken.models


class Token(rest_framework.authtoken.models.Token):
    """Custome Token model with ForeignKey relation to User model. Based on the DRF Token model."""

    key = models.CharField(_("Key"), max_length=40, db_index=True, unique=True, blank=True)
    """ Key attribute (the token string). It is no longer primary key, but still indexed and unique"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='auth_tokens',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    """ Relation to User model, it is a ForeignKey, so each user can have more than one token"""

    def __str__(self):
        """Define the string representation for objects of this class.

        Returns
        -------
        self.key: string
            The string representaiton, it is currently just the Token.key attribute
        """
        return self.key


class GlobalPermissions(models.Model):
    """Database-less model for custom Permissions."""

    class Meta:
        """The Meta class of this class."""

        managed = False
        """boolean: Define wether or not the model will be managed by the ORM (saved in the DB)"""

        permissions = (
            ('command.execute_command', 'Execute Commands'),
            ('command.run_script', 'Run and Requeue scripts in ScriptQueues'),
        )
        """((string, string)): Tuple defining permissions in the format ((<name>, <description>))"""
