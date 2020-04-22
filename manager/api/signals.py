from django.db.models.signals import post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from api.models import Token
import asyncio


@receiver(post_delete, sender=Token)
def handle_token_deletion(sender, **kwargs):
    """Receive signal when a Token is deleted and send a message to consumers subscribed to the Tokne's group,
    instructing them to logout.

    Parameters
    ----------
    sender: `object`
        class of the sender, in this case 'Token'
    kwargs: `dict`
        arguments dictionary sent with the signal. It contains the key 'instance' with the Token instance
        that was deleted
    """
    deleted_token = str(kwargs['instance'])
    groupname = 'token-{}'.format(deleted_token)
    payload = {'type': 'logout', 'message': ''}
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    if loop and loop.is_running():
        asyncio.create_task(get_channel_layer().group_send(groupname, payload))
    else:
        loop.run_until_complete(get_channel_layer().group_send(groupname, payload))
