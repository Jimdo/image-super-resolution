class UserImageUploadedEvent(object):
    """
    UserImageUploadedEvent record
    Args:
        url (str): url to access the image
    """
    def __init__(self, url=None):
        self.url = url


class UserImageProcessedEvent(object):
    """
    UserImageProcessedEvent record
    """
    def __init__(self, original_url=None, processed_bytes=None):
        self.original_url = original_url
        self.processed_bytes = processed_bytes
