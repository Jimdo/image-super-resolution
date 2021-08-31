from ISR.event_definitions import UserImageUploadedEvent, ImageSuperResolutionImageProcessedEvent
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
    return UserImageUploadedEvent(image_id=obj['id'],
                                  website_id=obj['website_id'],
                                  user_id=obj['user_id'],
                                  created_at=obj['created_at'],
                                  url=obj['url'],
                                  image_format=obj['format'],
                                  width=obj['width'],
                                  height=obj['height'], )


def user_image_processed_event_to_dict(event: ImageSuperResolutionImageProcessedEvent, ctx):
    """
    Converts a UserImageProcessedEvent to an object literal(dict).
    :param event:UserImageProcessedEvent
    :return: dict
    """
    return dict(original_url=event.original_url,
                bucket=event.bucket,
                object_key=event.object_key,
                created_at=event.created_at,
                processing_time_in_ms=event.processing_time_in_ms,
                processing_configuration=dict(
                    model_name=event.processing_configuration.model_name,
                    by_patch_of_size=event.processing_configuration.by_patch_of_size,
                    batch_size=event.processing_configuration.batch_size,
                    padding_size=event.processing_configuration.padding_size,
                ),
                user_image=dict(
                    id=event.user_image.id,
                    website_id=event.user_image.website_id,
                    user_id=event.user_image.user_id,
                    created_at=event.user_image.created_at,
                    url=event.user_image.url,
                    format=event.user_image.format,
                    width=event.user_image.width,
                    height=event.user_image.height,
                )
                )
