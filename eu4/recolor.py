import enum

from eu4 import border
from eu4 import image
from eu4 import mapfiles
from typing import Generator


# Special colors to use in recoloring
# DEFAULT - the default color of the province map
# SHADES_OF_WHITE - a unique shade of white per province
# TRANSPARENT - 0 opacity, displays as black unless using generateWithAlpha
class SpecialColor(enum.Enum):
    DEFAULT = 0
    SHADES_OF_WHITE = 1
    TRANSPARENT = 2


# Recolor a province map according to a mapping of province ID to color
# Does not modify the original province map
# Use the [] operator to set the color of a province
# (example: recolor[1] = (255, 0, 0) to set province 1 to red)
# Use any generate method to get the recolored image
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
    
    def __setitem__(self, province: int, color: tuple[int, int, int] | SpecialColor):
        provinceColor = self.definition.color.get(province)
        if provinceColor is None: # undefined province
            return
        self.colorMap[provinceColor] = color
        if type(color) is tuple:
            self.usedColors.add(color)
        elif color is SpecialColor.DEFAULT:
            self.usedColors.add(provinceColor)
    
    def _compileBitmap(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGBA:
        shadesOfWhiteGenerator = _shadesOfWhite(self.usedColors)
        bitmap = self.provinces.bitmap.copy().convert("RGBA")
        # Placing a 3-tuple into a 4-channel image automatically sets the alpha channel to 255 (opaque)
        # This lets us pretend that the image is still RGB
        for provinceMask in self.provinces.masks.values():
            color = provinceMask.color
            newColor = self.colorMap.get(color, default)
            if type(newColor) is tuple:
                bitmap.paste(newColor, provinceMask.boundingBox, provinceMask.bitmap)
            elif newColor is SpecialColor.DEFAULT:
                continue
            elif newColor is SpecialColor.SHADES_OF_WHITE:
                newColor = next(shadesOfWhiteGenerator)
                self.colorMap[color] = newColor # save the new shade of white
                bitmap.paste(newColor, provinceMask.boundingBox, provinceMask.bitmap)
            elif newColor is SpecialColor.TRANSPARENT:
                bitmap.paste((0, 0, 0, 0), provinceMask.boundingBox, provinceMask.bitmap)
        return image.RGBA(bitmap)
    
    # Provinces not in the mapping are set to default
    def generate(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGB:
        return self._compileBitmap(default).asRGB()

    # Use this to let SpecialColor.TRANSPARENT display as transparent
    def generateWithAlpha(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.RGBA:
        return self._compileBitmap(default)
    
    # Automatically turn the resulting image into a border image
    def generateBorders(self, default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT) -> image.Grayscale:
        borderMap = self.generate(default)
        return border.renderBorders(borderMap)
    
    # Automatically turn the resulting image into a double border image
    # Can additionally choose provinces to ignore ("filter") when generating borders, these provinces will
    #  not have their pixels turned into borders
    # This cannot be done with single borders as the borders technically only generate on one side of the
    #  province (up-left), and thus would be broken if filtered
    def generateDoubleBorders(self, 
            default: tuple[int, int, int] | SpecialColor = SpecialColor.DEFAULT,
            thick: bool = False,
            filterProvinces: list[int] = []
        ) -> image.Grayscale:

        borderMap = self.generate(default)
        borders = border.renderDoubleBorders(borderMap, thick)
        for filterProvince in filterProvinces:
            if filterProvince not in self.provinces.masks:
                continue
            mask = self.provinces.masks[filterProvince]
            borders.bitmap.paste(255, mask.boundingBox, mask.bitmap)
        return borders


# Generates increasingly darker shades of white
# Excludes the used colors in the set from being generated
def _shadesOfWhite(usedColors: set[tuple[int, int, int]]) -> Generator[tuple[int, int, int], None, None]:
    # yikes
    for maxValue in range(256):
        for r in range(maxValue + 1):
            for g in range(maxValue + 1):
                for b in range(maxValue + 1):
                    if (r == maxValue or g == maxValue or b == maxValue) and (r, g, b) not in usedColors:
                        yield (255 - r, 255 - g, 255 - b)
    raise ValueError("No unique shade of white available") # i doubt you'd ever use more than 16.7 million colors
