import enum
import PIL.Image as img

from eu4 import image
from eu4 import mapfiles
from typing import Generator


# Special colors to use in recoloring
# DEFAULT - the default color of the province map
# SHADES_OF_WHITE - a shade of white (unique among other SHADES_OF_WHITE colors)
class SpecialColor(enum.Enum):
    DEFAULT = 0
    SHADES_OF_WHITE = 1


# Recolor a province map according to a mapping of province ID to color
class Recolor:
    bitmap: img.Image
    definition: mapfiles.ProvinceDefinition
    colorMap: dict[tuple[int, int, int], tuple[int, int, int] | SpecialColor]
    def __init__(self, provinces: mapfiles.ProvinceMap, definition: mapfiles.ProvinceDefinition):
        self.bitmap = provinces.bitmap.copy()
        self.definition = definition
        self.colorMap = {}
    
    def __setitem__(self, province, color: tuple[int, int, int] | SpecialColor):
        provinceColor = self.definition[province]
        self.colorMap[provinceColor] = color
    
    # Provinces not in the mapping are set to default
    def generate(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGB:
        shadesOfWhiteGenerator = shadesOfWhite()
        for y in range(self.bitmap.height):
            for x in range(self.bitmap.width):
                pixelColor: tuple[int, int, int] = self.bitmap.getpixel((x, y)) # type: ignore
                newColor = self.colorMap.get(pixelColor, default)
                if type(newColor) is tuple:
                    self.bitmap.putpixel((x, y), newColor)
                elif newColor is SpecialColor.DEFAULT:
                    continue
                elif newColor is SpecialColor.SHADES_OF_WHITE:
                    newColor = next(shadesOfWhiteGenerator)
                    self.colorMap[pixelColor] = newColor # save the new shade of white
                    self.bitmap.putpixel((x, y), newColor)
        return image.RGB(self.bitmap)
    

# Turns the specified color on the province map transparent
def turnTransparent(provinces: mapfiles.ProvinceMap, color: tuple[int, int, int]) -> image.RGBA:
    transparent = img.new("RGBA", provinces.bitmap.size)
    for y in range(provinces.bitmap.height):
        for x in range(provinces.bitmap.width):
            pixelColor = provinces.bitmap.getpixel((x, y)) # type: ignore
            if pixelColor == color:
                transparent.putpixel((x, y), (0, 0, 0, 0))
    return image.RGBA(transparent)


# Generates increasingly darker shades of white
def shadesOfWhite() -> Generator[tuple[int, int, int], None, None]:
    # yikes
    for maxValue in range(0, 255 * 3):
        for r in range(0, maxValue + 1):
            for g in range(0, maxValue + 1):
                for b in range(0, maxValue + 1):
                    if r == maxValue or g == maxValue or b == maxValue:
                        yield (255 - r, 255 - g, 255 - b)
