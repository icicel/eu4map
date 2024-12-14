from eu4 import files
from eu4 import game
from eu4 import image
from PIL.Image import Resampling


class Canal(image.Palette):
    '''
    Represents a canal bitmap. When the canal is drawn, the game will paste this bitmap onto the river bitmap at the
    specified coordinates. This also means the palette of the canal bitmap should be the same as the river bitmap.
    '''

    name: str
    '''The name of the canal'''
    coords: tuple[int, int]
    '''The position of the tile (its top-left corner) in the river bitmap'''

    def __init__(self, game: game.Game, scope: files.Scope):
        '''
        :param game: The game object
        :param scope: The canal definition scope, as in `default.map`
        '''
        self.name = scope["name"]
        tilePath = game.getFile(f"map/{self.name}_river.bmp")
        self.load(tilePath)
        self.coords = (scope["x"], scope["y"])

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
    the highest possible province ID. (Note: In the actual file, this number is 1 higher for some reason)'''
    seas: list[int]
    '''The province IDs of all sea provinces'''
    rnw: list[int]
    '''The province IDs of all RNW provinces'''
    lakes: list[int]
    '''The province IDs of all lake provinces'''
    forcedCoasts: list[int]
    '''The province IDs of all "forced coastal" provinces. What this actually means is unclear'''
    canals: list[Canal]
    '''A list of all defined canals'''
    tree: list[int]
    '''The palette indices of the tree bitmap that should be used for terrain assignment'''
    provinceDefinition: str
    '''The filename of `mapfiles.ProvinceDefinition`. Is `definition.csv` in vanilla'''
    provinceMap: str
    '''The filename of `mapfiles.ProvinceMap`. Is `provinces.bmp` in vanilla'''
    positions: str
    '''The filename of `mapfiles.Positions`. Is `positions.txt` in vanilla'''
    terrainMap: str
    '''The filename of `mapfiles.TerrainMap`. Is `terrain.bmp` in vanilla'''
    riverMap: str
    '''The filename of the river bitmap. Is `rivers.bmp` in vanilla'''
    terrainDefinition: str
    '''The filename of `mapfiles.TerrainDefinition`. Is `terrain.txt` in vanilla'''
    heightmap: str
    '''The filename of `mapfiles.Heightmap`. Is `heightmap.bmp` in vanilla'''
    treeMap: str
    '''The filename of the tree bitmap. Is `trees.bmp` in vanilla'''
    continents: str
    '''The filename of the continent definition file. Is `continent.txt` in vanilla'''
    adjacencies: str
    '''The filename of `mapfiles.Adjacencies`. Is `adjacencies.csv` in vanilla'''
    climate: str
    '''The filename of `mapfiles.Climate`. Is `climate.txt` in vanilla'''
    regions: str
    '''The filename of the region definition file. Is `region.txt` in vanilla'''
    superregions: str
    '''The filename of the superregion definition file. Is `superregion.txt` in vanilla'''
    areas: str
    '''The filename of the area definition file. Is `area.txt` in vanilla'''
    provinceGroups: str
    '''The filename of the province group definition file. Is `provincegroup.txt` in vanilla'''
    ambientObjects: str
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
        self.seas = self.scope["sea_starts"]
        self.rnw = self.scope["only_used_for_random"]
        self.lakes = self.scope["lakes"]
        self.forcedCoasts = self.scope["force_coastal"]
        self.provinceDefinition = self.scope["definitions"]
        self.provinceMap = self.scope["provinces"]
        self.positions = self.scope["positions"]
        self.terrainMap = self.scope["terrain"]
        self.riverMap = self.scope["rivers"]
        self.terrainDefinition = self.scope["terrain_definition"]
        self.heightmap = self.scope["heightmap"]
        self.treeMap = self.scope["tree_definition"]
        self.continents = self.scope["continent"]
        self.adjacencies = self.scope["adjacencies"]
        self.climate = self.scope["climate"]
        self.regions = self.scope["region"]
        self.superregions = self.scope["superregion"]
        self.areas = self.scope["area"]
        self.provinceGroups = self.scope["provincegroup"]
        self.ambientObjects = self.scope["ambient_object"]
        self.seasons = self.scope["seasons"]
        self.tradeWinds = self.scope["trade_winds"]
        self.canals = [Canal(game, canalScope) for canalScope in self.scope.getAll("canal_definitions")]
        self.tree = self.scope["tree"]


class ProvinceMask(image.Binary):
    '''
    Efficient storage of a province's shape as a binary mask.
    '''

    color: tuple[int, int, int]
    '''The RGB color of the province'''
    boundingBox: tuple[int, int, int, int]
    '''The bounding box of the province, defined according to PIL's standard as (left, top, right + 1, 
    bottom + 1), aka (top-left pixel, bottom-right pixel + (1,1)). The rectangle defined by these coordinates
    is the smallest rectangle that contains the province's shape'''

    def __init__(self, color: tuple[int, int, int], coordinateList: tuple[list[int], list[int]]):
        '''
        :param color: The RGB color of the province
        :param coordinateList: Two lists, the first containing the x-coordinates of the pixels
        of the province, and the second containing the y-coordinates. These should be in the same order
        '''
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
        super().__init__((width, height), data)

class ProvinceMap(image.RGB):
    '''
    The province bitmap. Each RGB color represents a province.
    '''

    masks: dict[int, ProvinceMask]
    '''A dictionary of province IDs to their respective masks'''
    provinces: list[int]
    '''A list of all province IDs in the map'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap, definition: "ProvinceDefinition"):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        :param definition: The province definition object
        '''

        provincesPath = game.getFile(f"map/{defaultMap.provinceMap}")
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
            province = definition.province.get(color)
            if province is None: # undefined province
                continue
            self.masks[province] = ProvinceMask(color, coordinates)
            self.provinces.append(province)

    def double(self):
        '''
        Doubles the size of the bitmap and all masks. This can be useful when generating borders for very small provinces,
        as borders will be half as wide.
        '''

        self.bitmap = self.bitmap.resize((self.bitmap.width * 2, self.bitmap.height * 2), Resampling.NEAREST)
        for mask in self.masks.values():
            left, top, right, bottom = mask.boundingBox
            mask.boundingBox = (left * 2, top * 2, right * 2, bottom * 2)
            mask.bitmap = mask.bitmap.resize((mask.bitmap.width * 2, mask.bitmap.height * 2), Resampling.NEAREST)


class ProvinceDefinition(files.CsvFile):
    '''
    Maps province IDs to their RGB color in the province bitmap and vice versa.

    Be sure to use `dict.get` for null safety!
    '''

    color: dict[int, tuple[int, int, int]]
    '''A dictionary of province IDs to their respective RGB color'''
    province: dict[tuple[int, int, int], int]
    '''A dictionary of RGB colors to their respective province IDs'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        definitionPath = game.getFile(f"map/{defaultMap.provinceDefinition}")
        super().__init__(definitionPath)
        self.color = {}
        self.province = {}
        for row in self:
            if len(row) < 5:
                continue
            province, red, green, blue, *_ = row
            province = int(province)
            try:
                color = (int(red), int(green), int(blue))
            except ValueError: # see strToIntWeird below
                color = (_strToIntWeird(red), _strToIntWeird(green), _strToIntWeird(blue))
            self.color[province] = color
            self.province[color] = province

def _strToIntWeird(value: str) -> int:
    '''
    For some reason, the EU4 CSV parser can successfully detect and remove non-digits from the end of a number.
    This function is a reimplementation of that behavior.
    '''
    # I have only seen this feature in action in the definition.csv for Voltaire's Nightmare (where "104o"
    #   is successfully parsed as 104)
    # I have no idea why it exists or was ever deemed necessary to implement
    while not value[-1].isdigit():
        value = value[:-1]
    return int(value)


class Climate(files.ScopeFile):
    '''
    Defines climates and what provinces they apply to. Can be thought of as defining provinces' "passability", as
    wastelands are also defined here. Other than wastelands, the actual effect of having a certain climate is that
    a static modifier is applied to the province.
    
    The climate types defined are:
    - Wasteland (impassable)
    - Special climates: tropical, arid, arctic
    - Winter types: mild, normal, severe
    - Monsoon types: mild, normal, severe

    Additionally, this also defines the equator.
    '''

    wastelands: list[int]
    '''The province IDs of all wasteland (impassable) provinces'''
    tropical: list[int]
    '''The province IDs of all tropical provinces'''
    arid: list[int]
    '''The province IDs of all arid provinces'''
    arctic: list[int]
    '''The province IDs of all arctic provinces'''
    mildWinter: list[int]
    '''The province IDs of all provinces with mild winters'''
    normalWinter: list[int]
    '''The province IDs of all provinces with normal winters'''
    severeWinter: list[int]
    '''The province IDs of all provinces with severe winters'''
    mildMonsoon: list[int]
    '''The province IDs of all provinces with mild monsoons'''
    normalMonsoon: list[int]
    '''The province IDs of all provinces with normal monsoons'''
    severeMonsoon: list[int]
    '''The province IDs of all provinces with severe monsoons'''
    equator: int
    '''The Y-coordinate of the equator on the province map, supposedly. Unsure of its purpose, maybe to align GFX?'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        climatePath = game.getFile(f"map/{defaultMap.climate}")
        super().__init__(climatePath)
        self.tropical = self.scope["tropical"]
        self.arid = self.scope["arid"]
        self.arctic = self.scope["arctic"]
        self.mildWinter = self.scope["mild_winter"]
        self.normalWinter = self.scope["normal_winter"]
        self.severeWinter = self.scope["severe_winter"]
        self.wastelands = self.scope["impassable"]
        self.mildMonsoon = self.scope["mild_monsoon"]
        self.normalMonsoon = self.scope["normal_monsoon"]
        self.severeMonsoon = self.scope["severe_monsoon"]
        self.equator = self.scope["equator_y_on_province_image"]


class Heightmap(image.Grayscale):
    '''
    Represents the heightmap bitmap. Each pixel's value represents the height of the province, with 0 being the lowest
    and 255 being the highest.
    '''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        heightmapPath = game.getFile(f"map/{defaultMap.heightmap}")
        self.load(heightmapPath)


class ProvincePositions():
    '''
    A full set of positions of various province-related sprites and text, as (x, y) tuples. All refer to the same
    province.
    '''

    city: tuple[float, float]
    '''The position of the city sprawl'''
    unit: tuple[float, float]
    '''The position of the unit model'''
    text: tuple[float, float]
    '''The position of the province name text, if placed manually'''
    port: tuple[float, float]
    '''The position of the port model, if the province is coastal'''
    tradeNode: tuple[float, float]
    '''The position of the trade node model, if the province is a trade node's location'''
    battle: tuple[float, float]
    '''The position of the battling unit model'''
    tradeWind: tuple[float, float]
    '''The position of the trade wind sprite, if a trade wind is defined'''

    def __init__(self, positions: list[float]):
        '''
        :param positions: A list of 14 floats from the positions file
        '''
        self.city = (positions[0], positions[1])
        self.unit = (positions[2], positions[3])
        self.text = (positions[4], positions[5])
        self.port = (positions[6], positions[7])
        self.tradeNode = (positions[8], positions[9])
        self.battle = (positions[10], positions[11])
        self.tradeWind = (positions[12], positions[13])

class Positions(files.ScopeFile):
    '''
    Defines the positions of various sprites and text in each province.
    '''

    positions: dict[int, ProvincePositions]
    '''A dictionary of province IDs to their positions objects'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        positionsPath = game.getFile(f"map/{defaultMap.positions}")
        super().__init__(positionsPath)
        self.positions = {}
        for provinceId, provinceScope in self.scope:
            self.positions[int(provinceId)] = ProvincePositions(provinceScope["position"]) # type: ignore
    
    def __getitem__(self, key: int) -> ProvincePositions:
        '''
        :param key: The province ID
        :return: The positions object of the province
        '''
        return self.positions[key]


class AdjacencyType(files.NoneEnum):
    '''
    The type of adjacency between two provinces. The types `SEA`, `LAND`, `LAKE` and `RIVER` refer to what is being crossed
    and `CANAL` means that the adjacency is a canal.
    '''

    SEA = "sea"
    LAND = "land"
    LAKE = "lake"
    CANAL = "canal"
    RIVER = "river"
    NONE = None

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
    adjacencyType: AdjacencyType
    '''The type of adjacency'''
    line: tuple[int, int, int, int] | None
    '''The coordinates of the adjacency line graphic, as (startX, startY, stopX, stopY). If `None`, the exact line is
    undefined and is instead the shortest line between `Adjacency.fromProvince` and `Adjacency.toProvince`'''

    def __init__(self, raw: list[str]):
        '''
        :param raw: A row of adjacency data from `mapfiles.Adjacencies`
        '''
        self.fromProvince = int(raw[0])
        self.toProvince = int(raw[1])
        self.adjacencyType = AdjacencyType(raw[2])
        self.throughProvince = int(raw[3])
        self.line = (int(raw[4]), int(raw[5]), int(raw[6]), int(raw[7]))
        if self.line == (-1, -1, -1, -1):
            self.line = None

class Adjacencies(files.CsvFile):
    '''
    Defines additional connections between provinces in addition to the default adjacencies, such as straits and canals.
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
    '''
    The terrain bitmap. Each palette color represents a terrain type, defined in `mapfiles.TerrainDefinition`.
    '''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        terrainPath = game.getFile(f"map/{defaultMap.terrainMap}")
        self.load(terrainPath)


class TerrainGameplayType(files.NoneEnum):
    '''
    Relevant for various special effects related to broad terrain categories. For example, a province with the
    `PLAINS` gameplay type gives nomad nations a shock damage bonus. Since both Farmlands and Grasslands are
    defined as the gameplay type `PLAINS`, both will give the bonus.
    '''

    PTI = "pti"
    PLAINS = "plains"
    FOREST = "forest"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    JUNGLE = "jungle"
    MARSH = "marsh"
    DESERT = "desert"
    NONE = None

class TerrainSoundType(files.NoneEnum):
    '''
    Defines the type of ambient sound that plays when the camera is over the terrain.
    '''

    PLAINS = "plains"
    FOREST = "forest"
    DESERT = "desert"
    SEA = "sea"
    JUNGLE = "jungle"
    MOUNTAINS = "mountains"
    NONE = None

class Terrain:
    '''
    A terrain, or more accurately a terrain category.
    '''

    name: str
    '''The name of the terrain'''
    color: tuple[int, int, int]
    '''The RGB color of the terrain on the simple terrain mapmode'''
    gameplayType: TerrainGameplayType
    '''The gameplay type of the terrain'''
    soundType: TerrainSoundType
    '''The sound type of the terrain'''
    isWater: bool
    '''Whether the terrain should be treated as water'''
    isInlandSea: bool
    '''Whether the terrain should be treated as an inland sea (giving galleys a combat bonus among other
    things). Presumably also requires `Terrain.isWater` to be true'''
    overrides: list[int]
    '''A list of province IDs that should be assigned this terrain regardless of the automatic terrain assignment'''
    
    def __init__(self, name: str, scope: files.Scope):
        '''
        :param name: The name of the terrain
        :param scope: The terrain definition scope
        '''
        self.name = name
        self.color = tuple(scope.get("color", (0, 0, 0)))
        self.gameplayType = TerrainGameplayType(scope.get("type", None))
        self.soundType = TerrainSoundType(scope.get("sound_type", None))
        self.isWater = scope.get("is_water", False)
        self.isInlandSea = scope.get("inland_sea", False)
        self.overrides = scope.get("terrain_override", [])
    
    def __repr__(self) -> str:
        return f"Terrain({self.name})"

class TerrainDefinition(files.ScopeFile):
    '''
    Defines what terrain types are assigned to what colors on the terrain and tree bitmaps. Also defines
    provinces that should be hardcoded to have a specific terrain type.
    '''
    
    terrain: dict[int, Terrain]
    '''Maps palette indices in the terrain map to terrains'''
    tree: dict[int, Terrain]
    '''Maps palette indices in the tree map to terrains'''
    overrides: dict[int, Terrain]
    '''Maps province IDs to terrains, overriding the automatic terrain assignment. Not all provinces are
    necessarily overridden by this'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        terrainDefinitionPath = game.getFile(f"map/{defaultMap.terrainDefinition}")
        super().__init__(terrainDefinitionPath)
        terrainTags: dict[str, Terrain] = {}
        self.terrain = {}
        self.tree = {}
        self.overrides = {}
        for name, category in self.scope["categories"]:
            if not category: # empty category
                continue
            terrain = terrainTags[name] = Terrain(name, category)
            for overriddenProvince in terrain.overrides:
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
    croppedTerrain.paste(255, (0, 0), mask.inverted().bitmap)
    
    # Find the most common color in the province
    # Store as (count, palette index) tuples
    provinceTerrains: list[tuple[int, int]] = croppedTerrain.getcolors() # type: ignore
    provinceTerrains.sort(reverse=True)
    if provinceTerrains[0][1] == 255:
        provinceTerrains.pop(0)

    terrainIndex = provinceTerrains[0][1]
    return terrainDefinition.terrain[terrainIndex]
