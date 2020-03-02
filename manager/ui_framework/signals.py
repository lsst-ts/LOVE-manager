import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from manager import settings
from ui_framework.models import View

@receiver(post_delete, sender=View)
def hanlde_view_deletion(sender, **kwargs):
    """Receive signal when a View is deleted and delete its thumbnail image from disk.

    Parameters
    ----------
    sender: `object`
        class of the sender, in this case 'View'
    kwargs: `dict`
        arguments dictionary sent with the signal. It contains the key 'instance' with the View instance
        that was deleted
    """
    deleted_view = kwargs['instance']
    file_url = settings.MEDIA_BASE + deleted_view.thumbnail.url
    os.remove(file_url)