from django.db.models.signals import post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from api.models import Token


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
    async_to_sync(get_channel_layer().group_send)(
        'token-{}'.format(deleted_token),
        {'type': 'logout', 'message': ''}
    )
