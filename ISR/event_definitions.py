class UserImageUploadedEvent(object):
    """
    UserImageUploadedEvent record
    Args:
        url (str): url to access the image
    """

    def __init__(self, image_id, website_id, user_id, created_at, url, image_format, width, height):
        self.id = image_id
        self.website_id = website_id
        self.user_id = user_id
        self.created_at = created_at
        self.url = url
        self.format = image_format
        self.width = width
        self.height = height


class ImageSuperResolutionConfiguration(object):
    """
    ImageSuperResolutionConfiguration record
    """

    def __init__(self, model_name, by_patch_of_size, batch_size, padding_size):
        self.model_name = model_name
        self.by_patch_of_size = by_patch_of_size
        self.batch_size = batch_size
        self.padding_size = padding_size


class ImageSuperResolutionImageProcessedEvent(object):
    """
    ImageSuperResolutionImageProcessedEvent record
    """

    def __init__(self, original_url=None, bucket=None, object_key=None,
                 created_at=None, processing_time_in_ms=None,
                 user_image: UserImageUploadedEvent = None,
                 processing_configuration: ImageSuperResolutionConfiguration = None,
                 success=False):

        self.original_url = original_url
        self.bucket = bucket
        self.object_key = object_key
        self.user_image = user_image
        self.processing_configuration = processing_configuration
        self.created_at = created_at
        self.processing_time_in_ms = processing_time_in_ms
        self.success = success
