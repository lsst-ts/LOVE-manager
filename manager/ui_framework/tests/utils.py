"""Utilities for testing purposes."""
import json
from ui_framework.models import Workspace, View, WorkspaceView


def get_dict(obj):
    """Return a dictionary with the fields of a given object."""
    if type(obj) == Workspace:
        return {
            'id': obj.id,
            'name': obj.name,
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }
    if type(obj) == View:
        return {
            'id': obj.id,
            'name': obj.name,
            'data': json.dumps(obj.data),
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }
    if type(obj) == WorkspaceView:
        return {
            'id': obj.id,
            'view_name': obj.view_name,
            'view': obj.view.pk,
            'workspace': obj.workspace.pk,
            'creation_timestamp': obj.creation_timestamp,
            'update_timestamp': obj.update_timestamp,
        }
