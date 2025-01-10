
'''
Functions for rendering borders from the colored regions of an image. Primarily used for
rendering province borders from province maps.
'''

import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw

from eu4 import image


def renderBorders(provinces: image.RGB) -> image.Grayscale:
    '''
    Creates borders between same-colored regions (provinces). Since these are single borders,
    border pixels are effectively only placed on the north and west sides of a province. This
    makes it unsuitable for filtering, unlike `renderDoubleBorders`.

    :param provinces: The image to render borders using
    :return: The border image. A pixel is black if it's a border pixel and white otherwise
    '''
    shiftDown = _shiftDifference(provinces, 0, 1)
    shiftRight = _shiftDifference(provinces, 1, 0)
    shiftDownRight = _shiftDifference(provinces, 1, 1)
    differences = [shiftDown, shiftRight, shiftDownRight]
    return _differencesToBorders(differences)


def renderDoubleBorders(provinces: image.RGB, thick: bool = False) -> image.Grayscale:
    '''
    Creates borders between same-colored regions (provinces). Since these are double borders,
    border pixels are placed on all sides of a province. This means that if you filter certain
    colors to not be able to be borders, other borders will remain unbroken.

    :param provinces: The image to render borders using
    :param thick: Whether the borders should be doubled in width
    :return: The border image. A pixel is black if it's a border pixel and white otherwise
    '''
    shiftDown = _shiftDifference(provinces, 0, 1)
    shiftRight = _shiftDifference(provinces, 1, 0)
    shiftUp = _shiftDifference(provinces, 0, -1)
    shiftLeft = _shiftDifference(provinces, -1, 0)
    differences = [shiftDown, shiftRight, shiftUp, shiftLeft]
    if thick:
        shiftDownRight = _shiftDifference(provinces, 1, 1)
        shiftDownLeft = _shiftDifference(provinces, -1, 1)
        shiftUpRight = _shiftDifference(provinces, 1, -1)
        shiftUpLeft = _shiftDifference(provinces, -1, -1)
        differences += [shiftDownRight, shiftDownLeft, shiftUpRight, shiftUpLeft]
    return _differencesToBorders(differences)


def _differencesToBorders(images: list[img.Image]) -> image.Grayscale:
    '''
    Merge multiple pixel difference images into a single grayscale border image. This is done by
    merging all bands of the input images together, then inverting the result. Thus, black
    pixels in the resulting image mean that the pixel was non-black in at least one
    of the input images.

    :param images: The pixel difference images to merge
    :return: The border image
    '''
    result = img.new("L", images[0].size)
    for im in images:
        for band in im.split():
            result = chops.add(result, band)
    # merge all image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    borders = image.Grayscale(result)
    # set black to white and non-black to black
    return borders.flattened().inverted()


def _shiftDifference(provinces: image.RGB, shiftX: int, shiftY: int) -> img.Image:
    '''
    Returns the pixel difference between an image and a copy of itself shifted down-rightwards
    by the given amount. If a pixel is non-black in the difference image, it means its color
    changed between the original and the shifted image.

    :param provinces: The image to compare
    :param shiftX: The horizontal shift amount (positive is right)
    :param shiftY: The vertical shift amount (positive is down)
    '''
    image = provinces.bitmap
    shifted = image.transform(
        image.size, 
        img.Transform.AFFINE, 
        (1, 0, -shiftX, 0, 1, -shiftY))
    diff = chops.difference(image, shifted)
    # set pixels outside the shifted image's range to black
    drawing = draw.Draw(diff)
    if shiftX > 0:
        drawing.rectangle((0, 0, shiftX - 1, diff.height), fill=0)
    if shiftY > 0:
        drawing.rectangle((0, 0, diff.width, shiftY - 1), fill=0)
    if shiftX < 0:
        drawing.rectangle((diff.width + shiftX, 0, diff.width, diff.height), fill=0)
    if shiftY < 0:
        drawing.rectangle((0, diff.height + shiftY, diff.width, diff.height), fill=0)
    return diff
