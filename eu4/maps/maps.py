from eu4 import files
from eu4 import game


# Contains miscellaneous overarching map data
# Includes a definition of all sea provinces, rnw provinces, lake provinces and canals
# Also includes the filenames of other map files
class DefaultMap(files.ScopeFile):
    def __init__(self, game: game.Game):
        defaultMap = game.getFile("map/default.map")
        super().__init__(defaultMap)


# Maps provinces to their color in provinces.bmp
class ProvinceDefinition(files.CsvFile):
    color: dict[int, tuple[int, int, int]]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        definitionFilename = defaultMap["definitions"]
        definitionPath = game.getFile(f"map/{definitionFilename}")
        super().__init__(definitionPath)
        self.color = {}
        for province, red, green, blue, *_ in self:
            self.color[int(province)] = (int(red), int(green), int(blue))
    
    def __getitem__(self, key: int) -> tuple[int, int, int]:
        return self.color[key]


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
