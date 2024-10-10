import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw

# create a b&w border image from a province map
# its mode is "L" (grayscale)
def borderize(image: img.Image) -> img.Image:
    # create shift-difference images for each direction
    shiftDown = shiftDifference(image, 0, 1)
    shiftRight = shiftDifference(image, 1, 0)
    shiftDownRight = shiftDifference(image, 1, 1)
    # merge all 9 image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    bands = shiftDown.split() + shiftRight.split() + shiftDownRight.split()
    borders = bands[0]
    for band in bands[1:]:
        borders = chops.add(borders, band)
    # grayscale, then set black to white and non-black to black
    return borders.convert("L").point(lambda p: 0 if p else 255)

# create and overlay a border image on an image
def borderOverlay(image: img.Image) -> img.Image:
    borders = borderize(image)
    return img.composite(image, borders.convert("RGB"), borders)

# returns pixel difference between the map and itself shifted down-rightwards
# if a pixel is non-black in the difference image, 
# it means its color changed between the original and the shifted image
def shiftDifference(image: img.Image, shiftX: int, shiftY: int) -> img.Image:
    shifted = image.transform(
        image.size, 
        img.Transform.AFFINE, 
        (1, 0, -shiftX, 0, 1, -shiftY))
    diff = chops.difference(image, shifted)
    # set pixels outside the shifted image's range to black
    if shiftX:
        draw.Draw(diff).rectangle((0, 0, shiftX - 1, diff.height), fill=0)
    if shiftY:
        draw.Draw(diff).rectangle((0, 0, diff.width, shiftY - 1), fill=0)
    return diff
