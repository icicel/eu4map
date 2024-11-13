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
    def __init__(self, game: game.Game):
        defaultMap = game.getFile("map/default.map")
        super().__init__(defaultMap)
        self.width: int = self.scope["width"]
        self.height: int = self.scope["height"]
        self.maxProvinces: int = self.scope["max_provinces"]
        self.seaStarts: list[int] = self.scope["sea_starts"]
        self.onlyUsedForRandom: list[int] = self.scope["only_used_for_random"]
        self.lakes: list[int] = self.scope["lakes"]
        self.forceCoastal: list[int] = self.scope["force_coastal"]
        self.definitions: str = self.scope["definitions"]
        self.provinces: str = self.scope["provinces"]
        self.positions: str = self.scope["positions"]
        self.terrain: str = self.scope["terrain"]
        self.rivers: str = self.scope["rivers"]
        self.terrainDefinition: str = self.scope["terrain_definition"]
        self.heightmap: str = self.scope["heightmap"]
        self.treeDefinition: str = self.scope["tree_definition"]
        self.continent: str = self.scope["continent"]
        self.adjacencies: str = self.scope["adjacencies"]
        self.climate: str = self.scope["climate"]
        self.region: str = self.scope["region"]
        self.superregion: str = self.scope["superregion"]
        self.area: str = self.scope["area"]
        self.provincegroup: str = self.scope["provincegroup"]
        self.ambientObject: str = self.scope["ambient_object"]
        self.seasons: str = self.scope["seasons"]
        self.tradeWinds: str = self.scope["trade_winds"]
        self.canalDefinitions: list[CanalDefinition] = []
        for canalDefinition in self.scope.getAll("canal_definitions"):
            self.canalDefinitions.append(CanalDefinition(canalDefinition))
        self.tree: list[int] = self.scope["tree"]


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


class Adjacency:
    def __init__(self, adjacency: list[str]):
        self.fromProvince: int = int(adjacency[0])
        self.toProvince: int = int(adjacency[1])
        self.adjacencyType: str = adjacency[2]
        self.through: int = int(adjacency[3])
        self.startX: int = int(adjacency[4])
        self.startY: int = int(adjacency[5])
        self.stopX: int = int(adjacency[6])
        self.stopY: int = int(adjacency[7])

class Adjacencies(files.CsvFile):
    adjacencies: list[Adjacency]
    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        adjacenciesPath = game.getFile(f"map/{defaultMap.adjacencies}")
        super().__init__(adjacenciesPath)
        self.adjacencies = [Adjacency(adjacency) for adjacency in self]
    
    def __getitem__(self, key: int) -> Adjacency:
        return self.adjacencies[key]


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
        return f"TerrainCategory({self.name})"

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
