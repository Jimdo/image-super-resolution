from ISR.event_definitions import UserImageUploadedEvent, UserImageProcessedEvent
from ISR.utils.logger import get_logger

logger = get_logger(__name__)


def dict_to_user_image_uploaded_event(obj, ctx):
    """
    Converts object literal(dict) to a UserImageUploadedEvent instance.
    Args:
        obj (dict): Object literal(dict)
        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.
    """
    if obj is None:
        return None

    logger.info('building UserImageUploadedEvent with url %s' % obj['url'])
    return UserImageUploadedEvent(url=obj['url'])


def user_image_processed_event_to_dict(event: UserImageProcessedEvent, ctx):
    """
    Converts a UserImageProcessedEvent to an object literal(dict).
    :param event:UserImageProcessedEvent
    :return: dict
    """
    return dict(original_url=event.original_url,
                processed_bytes=event.processed_bytes)
