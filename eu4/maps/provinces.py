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


    # Recolors the province map according to a mapping of province ID to color
    # Provinces not in the mapping are left unchanged
    def recolor(self, mapping: dict[int, tuple[int, int, int]], definition: maps.ProvinceDefinition):
        print("Recoloring...")
        colorMapping = {definition[province]: color for province, color in mapping.items()}
        for x in range(self.bitmap.width):
            for y in range(self.bitmap.height):
                pixelColor: tuple[int, int, int] = self.bitmap.getpixel((x, y)) # type: ignore
                if pixelColor not in colorMapping:
                    continue
                self.bitmap.putpixel((x, y), colorMapping[pixelColor])


# A pixel is black if it's a border pixel and white otherwise
def borderize(provinces: ProvinceMap) -> image.Grayscale:
    # create shift-difference images for each direction
    shiftDown = shiftDifference(provinces, 0, 1)
    shiftRight = shiftDifference(provinces, 1, 0)
    shiftDownRight = shiftDifference(provinces, 1, 1)
    bands = [shiftDown, shiftRight, shiftDownRight]
    # merge all image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    borders = image.mergeBands(bands)
    # set black to white and non-black to black
    borders.flatten()
    borders.invert()
    return borders


# Places borders on all sides inside a province instead of just the north and west sides
# This means if you filter certain colors to not be able to be borders,
#  other borders will remain unbroken
# If thick is True, the borders are doubled in width
def doubleBorderize(provinces: ProvinceMap, thick: bool = False) -> image.Grayscale:
    shiftDown = shiftDifference(provinces, 0, 1)
    shiftRight = shiftDifference(provinces, 1, 0)
    shiftUp = shiftDifference(provinces, 0, -1)
    shiftLeft = shiftDifference(provinces, -1, 0)
    bands = [shiftDown, shiftRight, shiftUp, shiftLeft]
    if thick:
        shiftDownRight = shiftDifference(provinces, 1, 1)
        shiftDownLeft = shiftDifference(provinces, -1, 1)
        shiftUpRight = shiftDifference(provinces, 1, -1)
        shiftUpLeft = shiftDifference(provinces, -1, -1)
        bands += [shiftDownRight, shiftDownLeft, shiftUpRight, shiftUpLeft]
    borders = image.mergeBands(bands)
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
