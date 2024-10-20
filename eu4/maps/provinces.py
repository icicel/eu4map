import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw

from eu4 import game
from eu4 import image
from eu4.maps import maps


# A bitmap where each RGB color represents a province
class ProvinceMap(image.Bitmap):
    def __init__(self, game: game.Game, defaultMap: maps.DefaultMap):
        provincesFilename = defaultMap["provinces"]
        provincesPath = game.getFile(f"map/{provincesFilename}")
        super().__init__(provincesPath)


# A pixel is black if it's a border pixel and white otherwise
# Set light=true to ignore diagonal border pixels for lighter borders
def borderize(provinces: ProvinceMap, light: bool = False) -> image.Grayscale:
    # create shift-difference images for each direction
    shiftDown = shiftDifference(provinces, 0, 1)
    shiftRight = shiftDifference(provinces, 1, 0)
    bands = [shiftDown, shiftRight]
    if not light:
        shiftDownRight = shiftDifference(provinces, 1, 1)
        bands.append(shiftDownRight)
    # merge all image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    borders = image.mergeBands(bands)
    # set black to white and non-black to black
    borders.flatten()
    borders.invert()
    return borders


# Returns pixel difference between a province map and itself shifted down-rightwards
# If a pixel is non-black in the difference image, 
#  it means its color changed between the original and the shifted image
def shiftDifference(provinces: ProvinceMap, shiftX: int, shiftY: int) -> img.Image:
    image = provinces.bitmap
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
