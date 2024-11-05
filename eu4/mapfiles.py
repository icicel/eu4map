from eu4 import files
from eu4 import game
from eu4 import image
from PIL.Image import Resampling


# Contains miscellaneous overarching map data
# Includes a definition of all sea provinces, rnw provinces, lake provinces and canals
# Also includes the filenames of other map files
class DefaultMap(files.ScopeFile):
    def __init__(self, game: game.Game):
        defaultMap = game.getFile("map/default.map")
        super().__init__(defaultMap)


class ProvinceMask:
    color: tuple[int, int, int]
    boundingBox: tuple[int, int, int, int]
    mask: image.Binary
    def __init__(self, color: tuple[int, int, int], coordinateList: tuple[list[int], list[int]]):
        self.color = color
        xs, ys = coordinateList
        # the bottom-right corner is actually outside the bounding box
        self.boundingBox = left, top, right, bottom = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        width, height = right - left, bottom - top
        # Binary image creation works row-by-row, and when a row ends before a byte does,
        #  the rest of the byte is skipped
        # To avoid this, we need to pad the width
        paddedWidth = (width + 7) // 8 * 8 # round up to the nearest multiple of 8
        data = bytearray(paddedWidth * height)
        for x, y in zip(xs, ys):
            bit = (x - left) + (y - top) * paddedWidth
            byte = bit // 8
            bitInByte = bit % 8
            data[byte] |= 1 << (7 - bitInByte)
        self.mask = image.Binary((width, height), data)

# A bitmap where each RGB color represents a province
class ProvinceMap(image.RGB):
    masks: list[ProvinceMask]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        provincesFilename = defaultMap["provinces"]
        provincesPath = game.getFile(f"map/{provincesFilename}")
        self.load(provincesPath)
    
        # for each color, store all x and y coordinates of pixels with that color
        coordinateList: dict[tuple[int, int, int], tuple[list[int], list[int]]] = {}
        x, y = 0, 0
        for pixel in self.bitmap.getdata(): # type: ignore
            color: tuple[int, int, int] = pixel
            xs, ys = coordinateList.setdefault(color, ([], []))
            xs.append(x)
            ys.append(y)
            x += 1
            if x == self.bitmap.width: # clearer than modulo increment!
                x = 0
                y += 1

        # create ProvinceMask objects
        self.masks = [ProvinceMask(color, coordinates) for color, coordinates in coordinateList.items()]


    # Doubles the size of the bitmap and all masks
    # This can be useful for generating borders for very small provinces, as borders will be half as wide
    def double(self):
        self.bitmap = self.bitmap.resize((self.bitmap.width * 2, self.bitmap.height * 2), Resampling.NEAREST)
        for mask in self.masks:
            left, top, right, bottom = mask.boundingBox
            mask.boundingBox = (left * 2, top * 2, right * 2, bottom * 2)
            mask.mask.bitmap = mask.mask.bitmap.resize((mask.mask.bitmap.width * 2, mask.mask.bitmap.height * 2), Resampling.NEAREST)


# Maps provinces to their color in provinces.bmp
class ProvinceDefinition(files.CsvFile):
    color: dict[int, tuple[int, int, int]]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        definitionFilename = defaultMap["definitions"]
        definitionPath = game.getFile(f"map/{definitionFilename}")
        super().__init__(definitionPath)
        self.color = {}
        for province, red, green, blue, *_ in self:
            try:
                self.color[int(province)] = (int(red), int(green), int(blue))
            except ValueError: # see strToIntWeird below
                self.color[int(province)] = (_strToIntWeird(red), _strToIntWeird(green), _strToIntWeird(blue))
    
    def __getitem__(self, key: int) -> tuple[int, int, int]:
        return self.color[key]

# For some reason, the EU4 CSV parser can successfully detect
#  and remove non-digits from the end of a number
# I have only seen this feature in action in the definition.csv
#  for Voltaire's Nightmare (where "104o" is successfully parsed as 104)
# I have no idea why it exists or was ever deemed necessary to implement
def _strToIntWeird(value: str) -> int:
    while not value[-1].isdigit():
        value = value[:-1]
    return int(value)


# Contains arrays for:
# - tropical, arid, arctic
# - mild_winter, normal_winter, severe_winter
# - impassable
# - mild_monsoon, normal_monsoon, severe_monsoon
class Climate(files.ScopeFile):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        climateFilename = defaultMap["climate"]
        climatePath = game.getFile(f"map/{climateFilename}")
        super().__init__(climatePath)


class Heightmap(image.Grayscale):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        heightmapFilename = defaultMap["heightmap"]
        heightmapPath = game.getFile(f"map/{heightmapFilename}")
        self.load(heightmapPath)
