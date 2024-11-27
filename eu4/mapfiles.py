import enum

from eu4 import files
from eu4 import game
from eu4 import image
from PIL.Image import Resampling


class CanalDefinition:
    def __init__(self, scope: files.Scope):
        self.name: str = scope["name"]
        self.x: int = scope["x"]
        self.y: int = scope["y"]

# Contains miscellaneous overarching map data
# Includes a definition of all sea provinces, rnw provinces, lake provinces and canals
# Also includes the filenames of other map files
class DefaultMap(files.ScopeFile):
    '''
    Represents `default.map`. Contains miscellaneous overarching map data:
    - The width and height of the map
    - The maximum number of provinces
    - Definitions of sea provinces, RNW provinces, lake provinces, forced coastal provinces and canals
    - The filenames of other map files
    - What tree colors from `trees.bmp` should be used for terrain assignment
    '''

    width: int
    '''The width of the map'''
    height: int
    '''The height of the map'''
    maxProvinces: int
    '''The maximum number of provinces. Since province IDs are 1-indexed, this is equal to
    the highest possible province ID'''
    seaStarts: list[int]
    '''The province IDs of all sea provinces'''
    onlyUsedForRandom: list[int]
    '''The province IDs of all RNW provinces'''
    lakes: list[int]
    '''The province IDs of all lake provinces'''
    forceCoastal: list[int]
    '''The province IDs of all "forced coastal" provinces. What this actually means is unclear'''
    canalDefinitions: list[CanalDefinition]
    '''A list of all defined canals'''
    tree: list[int]
    '''The palette indices from `trees.bmp` that should be used for terrain assignment'''
    definitions: str
    '''The filename of the province definitions file. Is `definition.csv` in vanilla'''
    provinces: str
    '''The filename of the province bitmap. Is `provinces.bmp` in vanilla'''
    positions: str
    '''The filename of the province positions file. Is `positions.txt` in vanilla'''
    terrain: str
    '''The filename of the terrain bitmap. Is `terrain.bmp` in vanilla'''
    rivers: str
    '''The filename of the river bitmap. Is `rivers.bmp` in vanilla'''
    terrainDefinition: str
    '''The filename of the terrain definition file. Is `terrain.txt` in vanilla'''
    heightmap: str
    '''The filename of the heightmap file. Is `heightmap.bmp` in vanilla'''
    treeDefinition: str
    '''The filename of the tree bitmap. Is `trees.bmp` in vanilla'''
    continent: str
    '''The filename of the continent definition file. Is `continent.txt` in vanilla'''
    adjacencies: str
    '''The filename of the adjacency (strait) definition file. Is `adjacencies.csv` in vanilla'''
    climate: str
    '''The filename of the climate definition file. Is `climate.txt` in vanilla'''
    region: str
    '''The filename of the region definition file. Is `region.txt` in vanilla'''
    superregion: str
    '''The filename of the superregion definition file. Is `superregion.txt` in vanilla'''
    area: str
    '''The filename of the area definition file. Is `area.txt` in vanilla'''
    provincegroup: str
    '''The filename of the province group definition file. Is `provincegroup.txt` in vanilla'''
    ambientObject: str
    '''The filename of the ambient object definition file. Is `ambient_object.txt` in vanilla'''
    seasons: str
    '''The filename of the seasons definition file. Is `seasons.txt` in vanilla'''
    tradeWinds: str
    '''The filename of the trade winds definition file. Is `trade_winds.txt` in vanilla'''

    def __init__(self, game: game.Game):
        '''
        :param game: The game object
        '''
        defaultMap = game.getFile("map/default.map")
        super().__init__(defaultMap)
        self.width = self.scope["width"]
        self.height = self.scope["height"]
        self.maxProvinces = self.scope["max_provinces"] - 1 # important!
        self.seaStarts = self.scope["sea_starts"]
        self.onlyUsedForRandom = self.scope["only_used_for_random"]
        self.lakes = self.scope["lakes"]
        self.forceCoastal = self.scope["force_coastal"]
        self.definitions = self.scope["definitions"]
        self.provinces = self.scope["provinces"]
        self.positions = self.scope["positions"]
        self.terrain = self.scope["terrain"]
        self.rivers = self.scope["rivers"]
        self.terrainDefinition = self.scope["terrain_definition"]
        self.heightmap = self.scope["heightmap"]
        self.treeDefinition = self.scope["tree_definition"]
        self.continent = self.scope["continent"]
        self.adjacencies = self.scope["adjacencies"]
        self.climate = self.scope["climate"]
        self.region = self.scope["region"]
        self.superregion = self.scope["superregion"]
        self.area = self.scope["area"]
        self.provincegroup = self.scope["provincegroup"]
        self.ambientObject = self.scope["ambient_object"]
        self.seasons = self.scope["seasons"]
        self.tradeWinds = self.scope["trade_winds"]
        self.canalDefinitions = []
        for canalDefinition in self.scope.getAll("canal_definitions"):
            self.canalDefinitions.append(CanalDefinition(canalDefinition))
        self.tree = self.scope["tree"]


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
    masks: dict[int, ProvinceMask]
    provinces: list[int]
    def __init__(self, game: game.Game, defaultMap: DefaultMap, definition: "ProvinceDefinition"):
        provincesPath = game.getFile(f"map/{defaultMap.provinces}")
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

        # create provinces and masks
        self.masks = {}
        self.provinces = []
        for color, coordinates in coordinateList.items():
            province = definition.province[color]
            self.masks[province] = ProvinceMask(color, coordinates)
            self.provinces.append(province)


    # Doubles the size of the bitmap and all masks
    # This can be useful for generating borders for very small provinces, as borders will be half as wide
    def double(self):
        self.bitmap = self.bitmap.resize((self.bitmap.width * 2, self.bitmap.height * 2), Resampling.NEAREST)
        for mask in self.masks.values():
            left, top, right, bottom = mask.boundingBox
            mask.boundingBox = (left * 2, top * 2, right * 2, bottom * 2)
            mask.mask.bitmap = mask.mask.bitmap.resize((mask.mask.bitmap.width * 2, mask.mask.bitmap.height * 2), Resampling.NEAREST)


# Maps provinces to their color in provinces.bmp
class ProvinceDefinition(files.CsvFile):
    color: dict[int, tuple[int, int, int]]
    province: dict[tuple[int, int, int], int]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        definitionPath = game.getFile(f"map/{defaultMap.definitions}")
        super().__init__(definitionPath)
        self.color = {}
        self.province = {}
        for row in self:
            if len(row) < 5:
                continue
            province, red, green, blue, *_ = row
            try:
                color = (int(red), int(green), int(blue))
            except ValueError: # see strToIntWeird below
                color = (_strToIntWeird(red), _strToIntWeird(green), _strToIntWeird(blue))
            self.color[int(province)] = color
            self.province[color] = int(province)
    
    # Return None if not found
    def __getitem__(self, key: int) -> tuple[int, int, int] | None:
        return self.color.get(key, None)

# For some reason, the EU4 CSV parser can successfully detect
#  and remove non-digits from the end of a number
# I have only seen this feature in action in the definition.csv
#  for Voltaire's Nightmare (where "104o" is successfully parsed as 104)
# I have no idea why it exists or was ever deemed necessary to implement
def _strToIntWeird(value: str) -> int:
    while not value[-1].isdigit():
        value = value[:-1]
    return int(value)


class Climate(files.ScopeFile):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        climatePath = game.getFile(f"map/{defaultMap.climate}")
        super().__init__(climatePath)
        self.tropical: list[int] = self.scope["tropical"]
        self.arid: list[int] = self.scope["arid"]
        self.arctic: list[int] = self.scope["arctic"]
        self.mildWinter: list[int] = self.scope["mild_winter"]
        self.normalWinter: list[int] = self.scope["normal_winter"]
        self.severeWinter: list[int] = self.scope["severe_winter"]
        self.impassable: list[int] = self.scope["impassable"]
        self.mildMonsoon: list[int] = self.scope["mild_monsoon"]
        self.normalMonsoon: list[int] = self.scope["normal_monsoon"]
        self.severeMonsoon: list[int] = self.scope["severe_monsoon"]
        self.equatorYOnProvinceImage: int = self.scope["equator_y_on_province_image"]


class Heightmap(image.Grayscale):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        heightmapPath = game.getFile(f"map/{defaultMap.heightmap}")
        self.load(heightmapPath)


class ProvincePosition():
    def __init__(self, positionFloats: list[float]):
        positions = list(map(int, positionFloats))
        self.city: tuple[int, int] = (positions[0], positions[1])
        self.unit: tuple[int, int] = (positions[2], positions[3])
        self.text: tuple[int, int] = (positions[4], positions[5])
        self.port: tuple[int, int] = (positions[6], positions[7])
        self.tradeNode: tuple[int, int] = (positions[8], positions[9])
        self.battle: tuple[int, int] = (positions[10], positions[11])
        self.tradeWind: tuple[int, int] = (positions[12], positions[13])

class Positions(files.ScopeFile):
    positions: dict[int, ProvincePosition]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        positionsPath = game.getFile(f"map/{defaultMap.positions}")
        super().__init__(positionsPath)
        self.positions = {}
        for provinceId, provinceScope in self.scope:
            self.positions[int(provinceId)] = ProvincePosition(provinceScope["position"]) # type: ignore
    
    def __getitem__(self, key: int) -> ProvincePosition:
        return self.positions[key]


class AdjacencyType(enum.Enum):
    '''
    The type of adjacency between two provinces. The types `SEA`, `LAND`, `LAKE` and `RIVER` refer to what is being crossed
    and `CANAL` means that the adjacency is a canal.
    '''

    SEA = "sea"
    LAND = "land"
    LAKE = "lake"
    CANAL = "canal"
    RIVER = "river"

class Adjacency:
    '''
    A custom movement connection between two provinces.
    '''

    fromProvince: int
    '''The province ID of the origin province'''
    toProvince: int
    '''The province ID of the destination province'''
    throughProvince: int
    '''The province ID of the province that is being crossed. Utilized for strait blockade mechanics,
    likely does nothing if this isn't a `SEA` adjacency'''
    adjacencyType: AdjacencyType | None
    '''The type of adjacency. If `None`, no adjacency type is defined'''
    line: tuple[int, int, int, int] | None
    '''The coordinates of the adjacency line graphic, as (startX, startY, stopX, stopY). If `None`, the exact line is
    undefined and is instead the shortest line between `Adjacency.fromProvince` and `Adjacency.toProvince`'''

    def __init__(self, raw: list[str]):
        '''
        :param raw: A row of adjacency data from `mapfiles.Adjacencies`
        '''
        self.fromProvince: int = int(raw[0])
        self.toProvince: int = int(raw[1])
        try:
            self.adjacencyType = AdjacencyType(raw[2])
        except ValueError:
            self.adjacencyType = None
        self.throughProvince: int = int(raw[3])
        self.line = (int(raw[4]), int(raw[5]), int(raw[6]), int(raw[7]))
        if self.line == (-1, -1, -1, -1):
            self.line = None

class Adjacencies(files.CsvFile):
    '''
    Represents vanilla `adjacencies.csv`. Defines additional connections between provinces in addition to the
    default map connections, such as straits and canals.
    '''

    adjacencies: list[Adjacency]
    '''A list of all adjacencies in the file'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        adjacenciesPath = game.getFile(f"map/{defaultMap.adjacencies}")
        super().__init__(adjacenciesPath)
        self.adjacencies = [Adjacency(adjacency) for adjacency in self]


class TerrainMap(image.Palette):
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        terrainPath = game.getFile(f"map/{defaultMap.terrain}")
        self.load(terrainPath)


class Terrain:
    def __init__(self, name: str, scope: files.Scope):
        self.name: str = name
        self.color: tuple[int, int, int] = tuple(scope.get("color", (0, 0, 0)))
        self.terrainType: str | None = scope.get("type", None)
        self.soundType: str | None = scope.get("sound_type", None)
        self.isWater: bool = scope.get("is_water", False)
        self.inlandSea: bool = scope.get("inland_sea", False)
        self.terrainOverride: list[int] = scope.get("terrain_override", [])
    
    def __repr__(self) -> str:
        return f"Terrain({self.name})"

class TerrainDefinition(files.ScopeFile):
    terrain: dict[int, Terrain]
    tree: dict[int, Terrain]
    overrides: dict[int, Terrain]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        terrainDefinitionPath = game.getFile(f"map/{defaultMap.terrainDefinition}")
        super().__init__(terrainDefinitionPath)
        terrainTags: dict[str, Terrain] = {}
        self.terrain = {}
        self.tree = {}
        self.overrides = {}
        for name, category in self.scope["categories"]:
            terrain = terrainTags[name] = Terrain(name, category)
            for overriddenProvince in terrain.terrainOverride:
                if overriddenProvince in self.overrides:
                    continue # give priority to the terrain category that appears first
                self.overrides[overriddenProvince] = terrain
        for _, terrain in self.scope["terrain"]:
            colors: list[int] = terrain["color"]
            terrainTag: str = terrain["type"]
            for color in colors:
                self.terrain[color] = terrainTags[terrainTag]
        for _, treeTerrain in self.scope["tree"]:
            colors: list[int] = treeTerrain["color"]
            terrainTag: str = treeTerrain["terrain"]
            for color in colors:
                self.tree[color] = terrainTags[terrainTag]


def getTerrain(
        province: int,
        terrainMap: TerrainMap,
        terrainDefinition: TerrainDefinition,
        provinceMap: ProvinceMap
    ) -> Terrain:
    
    # Check for a manual terrain override
    # This is the best case scenario, the automatic terrain assignment is painful
    if province in terrainDefinition.overrides:
        return terrainDefinition.overrides[province]
    
    mask = provinceMap.masks[province]
    # Apply the mask to the terrain map
    croppedTerrain = terrainMap.bitmap.crop(mask.boundingBox)
    croppedTerrain.paste(255, (0, 0), mask.mask.inverted().bitmap)
    
    # Find the most common color in the province
    # Store as (count, palette index) tuples
    provinceTerrains: list[tuple[int, int]] = croppedTerrain.getcolors() # type: ignore
    provinceTerrains.sort(reverse=True)
    if provinceTerrains[0][1] == 255:
        provinceTerrains.pop(0)

    terrainIndex = provinceTerrains[0][1]
    return terrainDefinition.terrain[terrainIndex]
