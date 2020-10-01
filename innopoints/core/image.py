"""Image manipulation."""

from typing import Dict

from PIL import Image

from innopoints.core.helpers import abort


def crop(image: Image.Image, dimensions: Dict[str, str]):
    """Crop an image to the dimensions specified with keys 'x', 'y', 'width', 'height'."""
    if 'x' not in dimensions:
        return image

    try:
        # pylint: disable=invalid-name
        x = int(dimensions['x'])
        y = int(dimensions['y'])
        width = int(dimensions['width'])
        height = int(dimensions['height'])
    except KeyError:
        abort(400, {'message': 'Not enough data to perform the crop.'})
    else:
        if x != 0 or y != 0 or width != image.width or height != image.height:
            return image.crop((x, y, x + width, y + height))
        return image


SQUARE_THRESHOLD = 832
ANY_THRESHOLD = 1024

def shrink(image: Image.Image):
    """Shrink the image to reasonable dimensions."""
    if image.width == image.height:
        if image.width < SQUARE_THRESHOLD:
            return image
        new_size = (SQUARE_THRESHOLD, SQUARE_THRESHOLD)
    else:
        aspect_ratio = image.width / image.height
        if image.width > ANY_THRESHOLD:
            new_size = (ANY_THRESHOLD, int(ANY_THRESHOLD / aspect_ratio))
        elif image.height > ANY_THRESHOLD:
            new_size = (int(ANY_THRESHOLD * aspect_ratio), ANY_THRESHOLD)
        else:
            return image

    return image.resize(new_size)
