from eu4 import files
from eu4 import game
from eu4 import image


# Contains miscellaneous overarching map data
# Includes a definition of all sea provinces, rnw provinces, lake provinces and canals
# Also includes the filenames of other map files
class DefaultMap(files.ScopeFile):
    def __init__(self, game: game.Game):
        defaultMap = game.getFile("map/default.map")
        super().__init__(defaultMap)


# A bitmap where each RGB color represents a province
class ProvinceMap(image.RGB):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        provincesFilename = defaultMap["provinces"]
        provincesPath = game.getFile(f"map/{provincesFilename}")
        self.load(provincesPath)


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
