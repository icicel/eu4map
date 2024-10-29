import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw

from eu4 import image


# Shifting down-right, calculating the differences and then merging them creates neat borders
# A pixel is black if it's a border pixel and white otherwise
def borderize(provinces: image.RGB) -> image.Grayscale:
    shiftDown = shiftDifference(provinces, 0, 1)
    shiftRight = shiftDifference(provinces, 1, 0)
    shiftDownRight = shiftDifference(provinces, 1, 1)
    differences = [shiftDown, shiftRight, shiftDownRight]
    return differencesToBorders(differences)


# Places borders on all sides inside a province instead of just the north and west sides
# This means if you filter certain colors to not be able to be borders,
#  other borders will remain unbroken
# If thick is True, the borders are doubled in width
def doubleBorderize(provinces: image.RGB, thick: bool = False) -> image.Grayscale:
    shiftDown = shiftDifference(provinces, 0, 1)
    shiftRight = shiftDifference(provinces, 1, 0)
    shiftUp = shiftDifference(provinces, 0, -1)
    shiftLeft = shiftDifference(provinces, -1, 0)
    differences = [shiftDown, shiftRight, shiftUp, shiftLeft]
    if thick:
        shiftDownRight = shiftDifference(provinces, 1, 1)
        shiftDownLeft = shiftDifference(provinces, -1, 1)
        shiftUpRight = shiftDifference(provinces, 1, -1)
        shiftUpLeft = shiftDifference(provinces, -1, -1)
        differences += [shiftDownRight, shiftDownLeft, shiftUpRight, shiftUpLeft]
    return differencesToBorders(differences)


# Adds the bands of multiple pixel difference images together into a single grayscale image
# Black pixels in the result mean that the pixel is non-black in at least one of the input images
def differencesToBorders(images: list[img.Image]) -> image.Grayscale:
    result = img.new("L", images[0].size)
    for im in images:
        for band in im.split():
            result = chops.add(result, band)
    # merge all image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    borders = image.Grayscale(result)
    # set black to white and non-black to black
    borders.flatten()
    borders.invert()
    return borders


# Returns pixel difference between a province map and itself shifted down-rightwards
# If a pixel is non-black in the difference image, 
#  it means its color changed between the original and the shifted image
def shiftDifference(provinces: image.RGB, shiftX: int, shiftY: int) -> img.Image:
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
