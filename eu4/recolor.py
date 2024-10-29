import enum

from eu4 import image
from eu4 import mapfiles
from typing import Generator


# Special colors to use in recoloring
# DEFAULT - the default color of the province map
# SHADES_OF_WHITE - a unique shade of white
# TRANSPARENT - the color is turned transparent, displays as black unless using generateWithAlpha
class SpecialColor(enum.Enum):
    DEFAULT = 0
    SHADES_OF_WHITE = 1
    TRANSPARENT = 2


# Recolor a province map according to a mapping of province ID to color
# Does not modify the original province map
# Use the [] operator to set the color of a province
# (example: recolor[1] = (255, 0, 0) to set province 1 to red)
# Use generate() or generateWithAlpha() to get the recolored image
class Recolor:
    provinces: mapfiles.ProvinceMap
    definition: mapfiles.ProvinceDefinition
    colorMap: dict[tuple[int, int, int], tuple[int, int, int] | SpecialColor]
    usedColors: set[tuple[int, int, int]]
    def __init__(self, provinces: mapfiles.ProvinceMap, definition: mapfiles.ProvinceDefinition):
        self.provinces = provinces
        self.definition = definition
        self.colorMap = {}
        self.usedColors = set()
    
    def __setitem__(self, province, color: tuple[int, int, int] | SpecialColor):
        provinceColor = self.definition[province]
        self.colorMap[provinceColor] = color
        if type(color) is tuple:
            self.usedColors.add(color)
        elif color is SpecialColor.DEFAULT:
            self.usedColors.add(provinceColor)
    
    # Should not be called directly
    def compileBitmap(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGBA:
        shadesOfWhiteGenerator = shadesOfWhite(self.usedColors)
        bitmap = self.provinces.bitmap.copy().convert("RGBA")
        # Placing a 3-tuple into a 4-channel image automatically sets the alpha channel to 255 (opaque)
        # This lets us pretend that the image is still RGB
        for y in range(bitmap.height):
            for x in range(bitmap.width):
                pixelColor: tuple[int, int, int] = bitmap.getpixel((x, y))[:3] # type: ignore
                newColor = self.colorMap.get(pixelColor, default)
                if type(newColor) is tuple:
                    bitmap.putpixel((x, y), newColor)
                elif newColor is SpecialColor.DEFAULT:
                    continue
                elif newColor is SpecialColor.SHADES_OF_WHITE:
                    newColor = next(shadesOfWhiteGenerator)
                    self.colorMap[pixelColor] = newColor # save the new shade of white
                    bitmap.putpixel((x, y), newColor)
                elif newColor is SpecialColor.TRANSPARENT:
                    bitmap.putpixel((x, y), (0, 0, 0, 0))
        return image.RGBA(bitmap)
    
    # Provinces not in the mapping are set to default
    def generate(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGB:
        return self.compileBitmap(default).asRGB()

    # Use this to let SpecialColor.TRANSPARENT display as transparent
    def generateWithAlpha(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGBA:
        return self.compileBitmap(default)


# Generates increasingly darker shades of white
# Excludes the used colors in the set from being generated
def shadesOfWhite(usedColors: set[tuple[int, int, int]]) -> Generator[tuple[int, int, int], None, None]:
    # yikes
    for maxValue in range(0, 255 * 3):
        for r in range(0, maxValue + 1):
            for g in range(0, maxValue + 1):
                for b in range(0, maxValue + 1):
                    if (r == maxValue or g == maxValue or b == maxValue) and (r, g, b) not in usedColors:
                        yield (255 - r, 255 - g, 255 - b)
