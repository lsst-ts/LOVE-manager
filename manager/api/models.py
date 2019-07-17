from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
import rest_framework.authtoken.models


class Token(rest_framework.authtoken.models.Token):
    """ Custome Token model with ForeignKey relation to User model. Based on the DRF Token model """

    key = models.CharField(_("Key"), max_length=40, db_index=True, unique=True, blank=True)
    """ Key attribute (the token string). It is no longer primary key, but still indexed and unique"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='auth_tokens',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    """ Relation to User model, it is a ForeignKey, so each user can have more than one token"""

    def __str__(self):
        return self.key


class GlobalPermissions(models.Model):
    """ Database-less model for custom Permissions """

    class Meta:
        managed = False

        permissions = (
            ('Commands.execute_commands', 'Execute Commands'),
            ('ScriptQueue.run_scripts', 'Run and Requeue scripts in ScriptQueues'),
        )
