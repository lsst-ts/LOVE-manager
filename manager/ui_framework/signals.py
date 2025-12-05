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


import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from manager import settings
from ui_framework.models import View


@receiver(post_delete, sender=View)
def hanlde_view_deletion(sender, **kwargs):
    """Receive signal when a View is deleted
    and delete its thumbnail image from disk.

    Parameters
    ----------
    sender: `object`
        class of the sender, in this case 'View'
    kwargs: `dict`
        arguments dictionary sent with the signal.
        It contains the key 'instance' with the View instance that was deleted
    """
    deleted_view = kwargs["instance"]
    if deleted_view and deleted_view.thumbnail:
        file_url = settings.MEDIA_BASE + deleted_view.thumbnail.url
        try:
            os.remove(file_url)
        except FileNotFoundError:
            pass
    pass
