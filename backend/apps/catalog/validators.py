from django.conf import settings
from django.core.exceptions import ValidationError


def validate_product_image_size(image):
    if image.size > settings.PRODUCT_IMAGE_MAX_BYTES:
        max_mb = (
            settings.PRODUCT_IMAGE_MAX_BYTES
            / 1024
            / 1024
        )

        raise ValidationError(
            f"Product images cannot exceed {max_mb:g} MB."
        )
