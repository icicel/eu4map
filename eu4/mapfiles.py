
'''
This module contains classes for handling the various map files in EU4. These files define all aspects of the map
that can't be changed, such as terrain, climate, regions, rivers, etc etc (there's a lot).

The most important class for this module is `mapfiles.DefaultMap`, which represents the `default.map` file. All
other files will require a DefaultMap object to be loaded, as that is where their filenames are stored (yes, the
filenames can be changed).
'''

import math
import PIL.Image as img

from eu4 import files
from eu4 import game
from eu4 import image


class Canal(image.Palette):
    '''
    Represents a canal bitmap. When the canal is drawn in-game, the game will paste this bitmap onto the river map at the
    specified coordinates. This also means the palette of the canal bitmap should be the same as the river bitmap.
    '''

    name: str
    '''The name of the canal'''
    coords: tuple[int, int]
    '''The position of the tile (its top-left corner) in the river map'''

    def __init__(self, game: game.Game, scope: files.Scope):
        '''
        :param game: The game object
        :param scope: The canal definition scope, as in `default.map`
        '''
        self.name = scope.getConst("name")
        tilePath = game.getFile(f"map/{self.name}_river.bmp")
        self.load(tilePath)
        self.coords = (scope.getConst("x"), scope.getConst("y"))

class DefaultMap(files.ScopeFile):
    '''
    Represents `default.map`. Contains miscellaneous overarching map data:
    - The width and height of the map
    - The maximum number of provinces
    - Definitions of sea provinces, RNW provinces, lake provinces, forced coastal provinces and canals
    - The filenames of other map files
    '''

    width: int
    '''The width of the province map'''
    height: int
    '''The height of the province map'''
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
    provinceDefinition: str
    '''The filename of `mapfiles.ProvinceDefinition`. Is `definition.csv` in vanilla'''
    provinceMap: str
    '''The filename of `mapfiles.ProvinceMap`. Is `provinces.bmp` in vanilla'''
    positions: str
    '''The filename of `mapfiles.Positions`. Is `positions.txt` in vanilla'''
    terrainMap: str
    '''The filename of `mapfiles.TerrainMap`. Is `terrain.bmp` in vanilla'''
    riverMap: str
    '''The filename of `mapfiles.RiverMap`. Is `rivers.bmp` in vanilla'''
    terrainDefinition: str
    '''The filename of `mapfiles.TerrainDefinition`. Is `terrain.txt` in vanilla'''
    heightmap: str
    '''The filename of `mapfiles.Heightmap`. Is `heightmap.bmp` in vanilla'''
    treeMap: str
    '''The filename of `mapfiles.TreeMap`. Is `trees.bmp` in vanilla'''
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
        self.width = self.scope.getConst("width")
        self.height = self.scope.getConst("height")
        self.maxProvinces = self.scope.getConst("max_provinces") - 1 # the -1 is important!
        self.seas = self.scope.getArray("sea_starts", default=[])
        self.rnw = self.scope.getArray("only_used_for_random", default=[])
        self.lakes = self.scope.getArray("lakes", default=[])
        self.forcedCoasts = self.scope.getArray("force_coastal", default=[])
        self.provinceDefinition = self.scope.getConst("definitions")
        self.provinceMap = self.scope.getConst("provinces")
        self.positions = self.scope.getConst("positions")
        self.terrainMap = self.scope.getConst("terrain")
        self.riverMap = self.scope.getConst("rivers")
        self.terrainDefinition = self.scope.getConst("terrain_definition")
        self.heightmap = self.scope.getConst("heightmap")
        self.treeMap = self.scope.getConst("tree_definition")
        self.continents = self.scope.getConst("continent")
        self.adjacencies = self.scope.getConst("adjacencies")
        self.climate = self.scope.getConst("climate")
        self.regions = self.scope.getConst("region")
        self.superregions = self.scope.getConst("superregion")
        self.areas = self.scope.getConst("area")
        self.provinceGroups = self.scope.getConst("provincegroup")
        self.ambientObjects = self.scope.getConst("ambient_object")
        self.seasons = self.scope.getConst("seasons")
        self.tradeWinds = self.scope.getConst("trade_winds")
        self.canals = [Canal(game, canalScope) for canalScope in self.scope.getAll("canal_definitions")]


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
        Doubles the size of this map and all its masks. This can be useful when generating borders for very small provinces,
        as borders will be half as wide if generated from a double-size map.
        '''
        self.bitmap = self.bitmap.resize((self.bitmap.width * 2, self.bitmap.height * 2), img.Resampling.NEAREST)
        for mask in self.masks.values():
            left, top, right, bottom = mask.boundingBox
            mask.boundingBox = (left * 2, top * 2, right * 2, bottom * 2)
            mask.bitmap = mask.bitmap.resize((mask.bitmap.width * 2, mask.bitmap.height * 2), img.Resampling.NEAREST)


class ProvinceDefinition(files.CsvFile):
    '''
    Maps province IDs to their RGB color in the province bitmap and vice versa.
    '''

    color: dict[int, tuple[int, int, int]]
    '''A dictionary of province IDs to their respective RGB color'''
    province: dict[tuple[int, int, int], int]
    '''A dictionary of RGB colors to their respective province IDs. Note that the game allows invalid colors to be
    defined on the province map, so use `dict.get` for null safety'''

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
            if not province or not red or not green or not blue:
                continue
            province = int(province)
            try:
                color = (int(red), int(green), int(blue))
            except ValueError: # see _strToIntWeird below
                color = (_strToIntWeird(red), _strToIntWeird(green), _strToIntWeird(blue))
            self.color[province] = color
            self.province[color] = province

def _strToIntWeird(value: str) -> int:
    '''
    For some reason, the EU4 CSV parser can detect and remove non-digits from the end of a number. This
    function is a reimplementation of that behavior.

    :param value: The string to convert
    :return: The integer value of the string
    '''
    # I have only seen this feature in action in the definition.csv for Voltaire's Nightmare (where "104o"
    #  is successfully parsed as 104)
    # It would be odd to implement this behavior intentionally, so it's likely an unintentional quirk of the parser
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

    Also defines the "equator".
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
    equator: int | None
    '''The Y-coordinate of the equator on the province map, supposedly. Unsure of its purpose, maybe to align GFX?'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        climatePath = game.getFile(f"map/{defaultMap.climate}")
        super().__init__(climatePath)
        self.tropical = self.scope.getArray("tropical", default=[])
        self.arid = self.scope.getArray("arid", default=[])
        self.arctic = self.scope.getArray("arctic", default=[])
        self.mildWinter = self.scope.getArray("mild_winter", default=[])
        self.normalWinter = self.scope.getArray("normal_winter", default=[])
        self.severeWinter = self.scope.getArray("severe_winter", default=[])
        self.wastelands = self.scope.getArray("impassable", default=[])
        self.mildMonsoon = self.scope.getArray("mild_monsoon", default=[])
        self.normalMonsoon = self.scope.getArray("normal_monsoon", default=[])
        self.severeMonsoon = self.scope.getArray("severe_monsoon", default=[])
        self.equator = self.scope.getConst("equator_y_on_province_image", default=None)


class Heightmap(image.Grayscale):
    '''
    Represents the heightmap bitmap. Each pixel's value represents the height of the province, with 0 being the lowest
    and 255 being the highest. The sea level is at 94, so all values under that will be submerged.
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
    '''The position of the city sprawl model'''
    unit: tuple[float, float]
    '''The position of the unit model'''
    text: tuple[float, float]
    '''The position of the province name text, if placed manually'''
    port: tuple[float, float]
    '''The position of the port model, if the province is coastal'''
    tradeNode: tuple[float, float]
    '''The position of the trade node model, if the province is the location of a trade node'''
    battle: tuple[float, float]
    '''The position of the unit models in battle'''
    tradeWind: tuple[float, float]
    '''The position of the trade wind sprite, if a trade wind is defined for the province'''

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
            if type(provinceScope) is not files.Scope:
                raise ValueError(f"Invalid position data for province {provinceId}")
            self.positions[int(provinceId)] = ProvincePositions(provinceScope.getArray("position"))
    
    def __getitem__(self, key: int) -> ProvincePositions:
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
    likely does nothing if this isn't a `SEA`-type adjacency'''
    adjacencyType: AdjacencyType
    '''The type of adjacency'''
    line: tuple[int, int, int, int] | None
    '''The coordinates of the adjacency line graphic, as (startX, startY, stopX, stopY). If None, the line drawn
    is instead the shortest line between `Adjacency.fromProvince` and `Adjacency.toProvince`'''

    def __init__(self, raw: list[str]):
        '''
        :param raw: A row of adjacency data from the adjacencies file
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


class RiverMap(image.Palette):
    '''
    The river bitmap. Each palette index represents a river type which will be rendered on the map. The special
    indices are:
    - 0: River source
    - 1: Rivers merge
    - 2: Rivers split
    - 254/255: No river

    All other indices are rendered as plain rivers with increasing width the larger the index. In vanilla,
    indices 3, 4, 6, 9, 10 and 11 are used.
    '''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        riverPath = game.getFile(f"map/{defaultMap.riverMap}")
        self.load(riverPath)


class TreeMap(image.Palette):
    '''
    The tree bitmap. Each palette color represents a tree type which will be rendered on the map. Additionally, the
    tree bitmap is used for terrain assignment, where some tree types can affect the terrain type of a province.
    '''

    resizedBitmap: img.Image
    '''A copy of this map resized to the same dimensions as the terrain map'''

    treeTerrainMap: img.Image
    '''A copy of this map resized to the same dimensions as the terrain map, but using EU4's own (weird) algorithm.
    Used for terrain assignment'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        treePath = game.getFile(f"map/{defaultMap.treeMap}")
        self.load(treePath)
        terrainMapSize = (defaultMap.width, defaultMap.height)
        self.resizedBitmap = self.bitmap.resize(terrainMapSize, img.Resampling.NEAREST)

        # Resize the tree bitmap using the method used in EU4 when assigning terrain. I reverse-engineered this
        #  by creating one-pixel provinces and checking the terrain assignment in-game, so it may not match
        #  what the game actually does
        # Behaviorally, though, it is (as far as I can tell) identical to the game's algorithm, including
        #  in edge cases such as with non-integer scaling factors and at the edges of the map

        # As to why this algorithm is so unexpectedly complicated, there are likely two reasons:
        # 1. To match the tree models actually visible on the map (since the tree bitmap is used for that
        #  as well). This is why rows are shifted down, and why every other row is shifted left, as the
        #  tree models are placed in a hexagonal pattern
        # 2. So tree terrains won't entirely outshadow regular terrains. Since only alternating rows are
        #  actually placed, this leaves gaps for the terrain from the actual terrain bitmap to show through
        #  when this bitmap is placed on top of it

        # Create the new bitmap
        self.treeTerrainMap = img.new("P", terrainMapSize, 0)
        self.treeTerrainMap.putpalette(self.palette())

        # Calculate the scaling factors
        # (xRatio, yRatio) is the average size of the upscaled pixels
        xRatio = self.treeTerrainMap.width / self.bitmap.width
        yRatio = self.treeTerrainMap.height / self.bitmap.height

        # Remap the tree bitmap row by row
        for Y in range(self.bitmap.height):

            # Create the upscaled row's base image
            row = img.new("P", (self.treeTerrainMap.width, 1), 0)
            row.putpalette(self.palette())
            # If Y is even, shift the row left by half a pixel
            # (applied below)
            shift = 0.5 if Y % 2 == 0 else 0

            # Remap pixels in the row
            for X in range(self.bitmap.width):
                pixel: int = self.bitmap.getpixel((X, Y)) # type: ignore
                # Skip black pixels
                if pixel == 0:
                    continue
                # Place the pixel in the upscaled row, with a left shift if defined
                xStart = math.floor((X - shift) * xRatio)
                xEnd = math.ceil((X + 1 - shift) * xRatio) # no clue why this specifically is a ceil
                xEnd = min(xEnd, row.width - 1) # prevent out-of-bounds
                row.paste(pixel, (xStart, 0, xEnd, 1))

            # Calculate the upper (yEnd) and lower (yStart) bounds of the upscaled row
            # The row is shifted down by half a pixel
            yEnd = math.floor((Y + 0.5) * yRatio)
            yStart = math.floor((Y + 1.5) * yRatio)
            yStart = min(yStart, self.treeTerrainMap.height - 1) # prevent out-of-bounds
            
            # Paste copies of the upscaled row every other row starting from Ystart, going up to Yend
            y = yStart
            while y >= yEnd:
                # Mask out black pixels
                mask = row.point(lambda p: 1 if p != 0 else 0, mode="1")
                self.treeTerrainMap.paste(row, (0, y), mask)
                y -= 2
        
        # Done!


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
        self.color = tuple(scope.getArray("color", default=(255, 255, 255)))
        self.gameplayType = TerrainGameplayType(scope.getConst("type", default=None))
        self.soundType = TerrainSoundType(scope.getConst("sound_type", default=None))
        self.isWater = scope.getConst("is_water", default=False)
        self.isInlandSea = scope.getConst("inland_sea", default=False)
        self.overrides = scope.getArray("terrain_override", default=[])
    
    def __repr__(self) -> str:
        return f"Terrain({self.name})"

class TerrainDefinition(files.ScopeFile):
    '''
    Defines what terrain types are assigned to what colors on the terrain and tree bitmaps. Also defines
    provinces that should be hardcoded to have a specific terrain type.
    '''
    
    terrainIndex: dict[int, Terrain]
    '''Maps palette indices in the terrain map to terrains'''
    treeIndex: dict[int, Terrain]
    '''Maps palette indices in the tree map to terrains'''
    overrides: dict[int, Terrain]
    '''Maps province IDs to terrains, overriding the automatic terrain assignment. Not all provinces are
    necessarily overridden by this'''
    terrains: list[Terrain]
    '''A list of all defined terrains'''
    defaultTerrain: Terrain
    '''Is always `pti`. Used when a province cannot be assigned a terrain'''

    def __init__(self, game: game.Game, defaultMap: DefaultMap):
        '''
        :param game: The game object
        :param defaultMap: The `default.map` object
        '''
        terrainDefinitionPath = game.getFile(f"map/{defaultMap.terrainDefinition}")
        super().__init__(terrainDefinitionPath)
        terrainTags: dict[str, Terrain] = {}
        self.terrainIndex = {}
        self.treeIndex = {}
        self.overrides = {}
        self.terrains = []

        # Create the terrain objects
        for name, category in self.scope.getScope("categories", default=[]):
            if category == "":
                category = files.Scope()
            if type(category) is not files.Scope:
                raise ValueError(f"Invalid terrain category: {category}")
            terrain = terrainTags[name] = Terrain(name, category)
            self.terrains.append(terrain)
            for overriddenProvince in terrain.overrides:
                if overriddenProvince in self.overrides:
                    continue # give priority to the terrain category that appears first
                self.overrides[overriddenProvince] = terrain
        self.defaultTerrain = terrainTags["pti"]

        # Map terrains to indices in the terrain and tree bitmaps
        for _, terrainScope in self.scope.getScope("terrain"):
            if type(terrainScope) is not files.Scope:
                raise ValueError(f"Invalid graphical terrain: {terrainScope}")
            colors: list[int] = terrainScope.getArray("color")
            terrainTag: str = terrainScope.getConst("type")
            for color in colors:
                self.terrainIndex[color] = terrainTags[terrainTag]
        for _, treeScope in self.scope.getScope("tree"):
            if type(treeScope) is not files.Scope:
                raise ValueError(f"Invalid tree terrain: {treeScope}")
            colors: list[int] = treeScope.getArray("color")
            terrainTag: str = treeScope.getConst("terrain")
            for color in colors:
                self.treeIndex[color] = terrainTags[terrainTag]

    # Hell On Earth
    def getTerrain(
            self,
            province: int,
            defaultMap: DefaultMap,
            terrainMap: TerrainMap,
            provinceMap: ProvinceMap,
            treeMap: TreeMap,
            riverMap: RiverMap,
            debug: bool = False
        ) -> Terrain:
        '''
        Gets the terrain of a province. This is a complex process that involves checking the province on all
        bitmaps and applying various rules to determine the terrain. That is, unless the province has a manual
        terrain override, in which case that is returned.

        :param province: The province ID
        :param defaultMap: The `default.map` object
        :param terrainMap: The terrain bitmap
        :param provinceMap: The province bitmap
        :param treeMap: The tree bitmap
        :param riverMap: The river bitmap
        :param debug: Whether to print debug information
        :return: The terrain of the province
        '''
        
        # Check for a manual terrain override
        # This is the best case scenario, the automatic terrain assignment is painful
        # Luckily about half of all provinces have overrides
        if province in self.overrides:
            return self.overrides[province]
        
        mask = provinceMap.masks[province]
        
        # Create a crop of the terrain, tree and river maps where the province is
        rawTerrainCrop = terrainMap.bitmap.crop(mask.boundingBox)
        rawTreeCrop = treeMap.treeTerrainMap.crop(mask.boundingBox)
        riverCrop = riverMap.bitmap.crop(mask.boundingBox)

        # Apply the mask to the tree and terrain crops, clearing pixels outside the province
        rawTerrainCrop.paste(255, (0, 0), mask.inverted().bitmap)
        rawTreeCrop.paste(0, (0, 0), mask.inverted().bitmap)
        terrainCrop = rawTerrainCrop.copy()
        treeCrop = rawTreeCrop.copy()

        # Mask the tree crop over the terrain crop, clearing terrain pixels where there is a defined tree
        # Ensures there is no overlap between the two when counting colors
        treeMask = treeCrop.point(lambda p: 1 if p != 0 else 0, mode="1")
        terrainCrop.paste(255, (0, 0), treeMask)

        # Mask out river pixels from the terrain and tree crops
        # Only mask out rivers wider than index 3
        riverMask = riverCrop.point(lambda p: 1 if p > 3 and p < 254 else 0, mode="1") # type: ignore
        terrainCrop.paste(255, (0, 0), riverMask)
        treeCrop.paste(0, (0, 0), riverMask)

        # Clear tree colors that are not valid for terrain assignment (hardcoded)
        # These map to "palms" and "savana" in the terrain definition
        invalidTreeColors = [12, 27, 28, 29, 30]
        treeCrop = treeCrop.point(lambda p: 0 if p in invalidTreeColors else p)
        
        # Find the most common terrain in the province
        # Also store a "tiebreaker" value per terrain, which is just the lowest index in the terrain map
        terrainCount: dict[Terrain, int] = {}
        terrainTiebreaker: dict[Terrain, int] = {}
        provinceTerrains: list[tuple[int, int]] = terrainCrop.getcolors() # type: ignore
        for count, index in provinceTerrains:
            if index == 255 or index not in self.terrainIndex:
                continue
            terrain = self.terrainIndex[index]
            terrainCount[terrain] = terrainCount.get(terrain, 0) + count
            terrainTiebreaker[terrain] = min(terrainTiebreaker.get(terrain, index), index)
        provinceTrees: list[tuple[int, int]] = treeCrop.getcolors() # type: ignore
        for count, index in provinceTrees:
            if index == 0 or index not in self.treeIndex:
                continue
            terrain = self.treeIndex[index]
            terrainCount[terrain] = terrainCount.get(terrain, 0) + count * 2 # trees count double
            # presumably the tree index has a lower priority than the terrain index when
            #  it comes to tiebreaking, so we add 255 to it
            terrainTiebreaker[terrain] = min(terrainTiebreaker.get(terrain, index + 255), index + 255)
        
        # Sort the terrains by count, then by tiebreaker
        terrains = list(terrainCount.keys())
        terrains.sort(key=lambda terrain: terrainTiebreaker[terrain])
        terrains.sort(key=lambda terrain: terrainCount[terrain], reverse=True)
        
        if debug:
            import time
            def show(image: img.Image):
                image.show()
                time.sleep(1)
            show(rawTerrainCrop)
            show(rawTreeCrop)
            show(treeMask)
            show(riverMask)
            show(terrainCrop)
            show(treeCrop)
            print(provinceTerrains)
            print(provinceTrees)
            print(terrainCount)
            print(terrainTiebreaker)
            print(terrains)

        # Find the most common color that is a valid terrain
        while True:
            if not terrains: # no valid terrains
                return self.defaultTerrain
            terrain = terrains.pop(0)
            # Ignore water terrains if the province is not a sea
            # Ignore land terrains if the province is a sea
            if (terrain.isWater) != (province in defaultMap.seas):
                continue
            return terrain

        # TODO: The current algorithm is not perfect. At the moment, every vanilla
        #  province is assigned the correct terrain, but in many mods some provinces
        #  slip by. This is most visible in Atlas Novum, since it has 15000 provinces.
        #  Overall, though, accuracy is 99%+.
        # One possibility is that not all trees may count double, or that some may be
        #  weighted with a different factor such as x1.5. Could be worth investigating.
