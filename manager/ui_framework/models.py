"""
Defines the Django models for this app.

For more information see:
https://docs.djangoproject.com/en/2.2/topics/db/models/
"""
from django.db import models


class BaseModel(models.Model):
    """Base Model for the models of this app."""

    class Meta:
        """Define attributes of the Meta class."""

        abstract = True
        """Make this an abstract class in order to be used as an enhanced base model"""

    creation_timestamp = models.DateTimeField(
        auto_now_add=True, editable=False,
        verbose_name='Creation time'
    )
    """Creation timestamp, autogenerated upon creation"""

    update_timestamp = models.DateTimeField(
        auto_now=True, editable=False,
        verbose_name='Last Updated'
    )
    """Update timestamp, autogenerated upon creation and autoupdated on every update"""


class View(BaseModel):
    """View Model."""

    name = models.CharField(max_length=20)
    """The name of the View. e.g 'My View'"""

    def __str__(self):
        """Redefine how objects of this class are transformed to string."""
        return self.name


class Workspace(BaseModel):
    """Workspace Model."""

    name = models.CharField(max_length=20)
    """The name of the Workspace. e.g 'My Workspace'"""

    views = models.ManyToManyField(View, through='WorkspaceView', related_name='workspaces')

    def __str__(self):
        """Redefine how objects of this class are transformed to string."""
        return self.name


class WorkspaceView(BaseModel):
    """WorkspaceView Model, that relates a Works with a View."""

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='wokspace_views')
    """The corresponding Workspace"""

    view = models.ForeignKey(View, on_delete=models.CASCADE, related_name='wokspace_views')
    """The corresponding View"""

    view_name = models.CharField(max_length=20, blank=True)
    """The custom name for the View within the Workspace"""

    def __str__(self):
        """Redefine how objects of this class are transformed to string."""
        if self.view_name and self.view_name != '':
            return '{}: {} - {}'.format(self.view_name, self.workspace.name, self.view.name)