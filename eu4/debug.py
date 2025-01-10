import random
import re
import os
import PIL.Image as img
import PIL.ImageChops as chops

from eu4 import game
from eu4 import image
from eu4 import mapfiles
from eu4 import presets
from eu4 import recolor
from eu4 import render


def generatePresets(outputDir: str = "test", modloader: bool = False, mod: str | int | list[str | int] | None = None):
    '''
    Run every preset and save the output images in the specified directory.

    :param outputDir: The directory to save the output images in
    :param modloader: Whether to load the game with the modloader enabled
    :param mod: The mod or mods to load
    '''

    print("Loading game...")
    eu4 = game.Game(modloader, mod)

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(eu4)
    definition = mapfiles.ProvinceDefinition(eu4, defaultMap)
    climate = mapfiles.Climate(eu4, defaultMap)
    heightmap = mapfiles.Heightmap(eu4, defaultMap)
    terrain = mapfiles.TerrainMap(eu4, defaultMap)
    terrainDefinition = mapfiles.TerrainDefinition(eu4, defaultMap)
    tree = mapfiles.TreeMap(eu4, defaultMap)
    river = mapfiles.RiverMap(eu4, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, definition)

    presets.blank(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output.png")
    presets.landProvinces(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output1.png")
    presets.template(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output2.png")
    presets.colorableTemplate(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output3.png")
    presets.heightmapCoast(defaultMap, provinceMap, definition, heightmap).save(f"{outputDir}/output4.png")
    presets.simpleTerrain(defaultMap, provinceMap, definition, climate, terrainDefinition, terrain, tree, river).save(f"{outputDir}/output5.png")
    render.renderTerrainLegend(terrain, terrainDefinition, tree).save(f"{outputDir}/output50.png")
    render.renderMasks(provinceMap).save(f"{outputDir}/output0.png")
    render.renderMasksWithTerrain(provinceMap, terrain).save(f"{outputDir}/output00.png")


def testAllMods():
    '''
    Run all presets on all installed mods that edit the map. The respective outputs are saved in `test/[modname]`.
    '''

    print("Finding mods...")
    mods = game.getAllMods(game.DOCUMENTS_DIRECTORY)

    for mod in mods:
        if not os.path.exists(f"{mod.path}/map/default.map"):
            # mod doesn't edit the map
            continue
        
        dirname = re.sub(r"^_+|_+$", "", re.sub(r"[^a-z0-9.']+", "_", mod.name.lower()))
        if os.path.exists(f"test/{dirname}/output00.png"):
            # already tested the mod
            continue
        os.makedirs(f"test/{dirname}", exist_ok=True)
        
        print(f"*** Testing mod {mod.name} ({mod.technicalName})")
        generatePresets(f"test/{dirname}", mod=mod.path)


def generateTerrainTest(modloader: bool = False, mod: str | int | list[str | int] | None = None):
    '''
    To effectively test terrain assignments, you have to create one-pixel provinces and then check
    what terrain is assigned to them. This function generates a few images to help with this process.

    More specifically, it picks a random selection of land provinces, replaces them with wasteland,
    and then creates a square with each chosen province represented by a pixel of its color. This
    square can then be pasted on the province map wherever the underlying terrain should be tested.

    :param modloader: Whether to load the game with the modloader enabled
    :param mod: The mod or mods to load
    '''

    print("Loading game...")
    eu4 = game.Game(modloader, mod)

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(eu4)
    definition = mapfiles.ProvinceDefinition(eu4, defaultMap)
    climate = mapfiles.Climate(eu4, defaultMap)
    terrain = mapfiles.TerrainMap(eu4, defaultMap)
    tree = mapfiles.TreeMap(eu4, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, definition)
    
    SIZE = 30
    # grab X arbitrary land provinces
    nonland = defaultMap.seas + defaultMap.lakes + climate.wastelands
    land = [province for province in provinceMap.provinces if province not in nonland]
    chosenProvinces = random.sample(land, SIZE*SIZE)
    # grab an arbitrary wasteland province's color
    wastelandColor = definition.color[climate.wastelands[0]]

    print("Recoloring provinces...")
    # color the chosen provinces in the wasteland's color
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for province in chosenProvinces:
        recolorBackground[province] = wastelandColor
    provinceImage = recolorBackground.generate().bitmap

    print("Overlaying trees...")
    # overlay the tree map on the terrain map (ignoring black (palette index 0) pixels)
    terrainImage = terrain.bitmap.convert("RGB")
    terrainImage.paste(tree.resizedBitmap.convert("RGB"), mask=tree.resizedBitmap.point(lambda p: 1 if p else 0, mode="1"))

    print("Generating pixels...")
    # generate a pixel of color for each chosen province
    # (this can then be placed in the province image where the terrain should be tested)
    pixelImage = img.new("RGB", (SIZE, SIZE))
    pixelImage.putdata([definition.color[province] for province in chosenProvinces])

    provinceImage.show()
    terrainImage.show()
    pixelImage.show()


def testTreeMapRatios():
    '''
    Print the size ratio of the terrain and tree maps for the vanilla game and all mods that edit the map.
    '''

    print("Finding mods...")
    mods = game.getAllMods(game.DOCUMENTS_DIRECTORY)

    vanillaGame = game.Game()

    defaultMap = mapfiles.DefaultMap(vanillaGame)
    tree = mapfiles.TreeMap(vanillaGame, defaultMap)
    provinceMapSize = (defaultMap.width, defaultMap.height)
    treeMapSize = (tree.bitmap.width, tree.bitmap.height)
    sizeRatio = (provinceMapSize[0] / treeMapSize[0], provinceMapSize[1] / treeMapSize[1])

    print(f"Vanilla")
    print(f"\t{sizeRatio}")

    for mod in mods:
        if not os.path.exists(f"{mod.path}/map/default.map"):
            # mod doesn't edit the map
            continue
        
        moddedGame = game.Game(mod=mod.path)

        defaultMap = mapfiles.DefaultMap(moddedGame)
        tree = mapfiles.TreeMap(moddedGame, defaultMap)
        provinceMapSize = (defaultMap.width, defaultMap.height)
        treeMapSize = (tree.bitmap.width, tree.bitmap.height)
        sizeRatio = (provinceMapSize[0] / treeMapSize[0], provinceMapSize[1] / treeMapSize[1])

        print(f"{mod.name}")
        print(f"\t{sizeRatio}")


def generateOverrideMap(modloader: bool = False, mod: str | int | list[str | int] | None = None):
    '''
    Create a map showing land provinces with manual terrain assignments in white, and all other land provinces in red.

    :param modloader: Whether to load the game with the modloader enabled
    :param mod: The mod or mods to load
    '''

    print("Loading game...")
    eu4 = game.Game(modloader, mod)

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(eu4)
    definition = mapfiles.ProvinceDefinition(eu4, defaultMap)
    climate = mapfiles.Climate(eu4, defaultMap)
    terrainDefinition = mapfiles.TerrainDefinition(eu4, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, definition)

    print("Recoloring provinces...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    waters: set[int] = set(defaultMap.seas + defaultMap.lakes)
    wastelands: set[int] = set(climate.wastelands)
    for province in provinceMap.provinces:
        if province in waters:
            recolorBackground[province] = (68, 107, 163)
        elif province in wastelands:
            recolorBackground[province] = (94, 94, 94)
        elif province in terrainDefinition.overrides:
            recolorBackground[province] = (255, 255, 255)
        else:
            recolorBackground[province] = (255, 0, 0)
    backgroundMap = recolorBackground.generate()

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonland in defaultMap.seas + defaultMap.lakes + climate.wastelands:
        recolorBorders[nonland] = (0, 0, 0)
    borders = recolorBorders.generateBorders()

    print("Overlaying...")
    image.overlay(backgroundMap, borders.asRGB(), borders).bitmap.show()


def testTerrainAssignments():
    '''
    Compare the `simpleTerrain` preset with an actual screenshot of the simple terrain mapmode. Prints
    a list of (land) provinces where the colors differ between the two images.
    
    Intended use is to load a mod that changes the map, take an F10 screenshot of the simple terrain
    mapmode in-game, and run this function to see how accurately the screenshot has been recreated.
    '''

    print("Loading game...")
    eu4 = game.Game(modloader=True)

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(eu4)
    provinceDef = mapfiles.ProvinceDefinition(eu4, defaultMap)
    climate = mapfiles.Climate(eu4, defaultMap)
    terrainMap = mapfiles.TerrainMap(eu4, defaultMap)
    terrainDef = mapfiles.TerrainDefinition(eu4, defaultMap)
    treeMap = mapfiles.TreeMap(eu4, defaultMap)
    riverMap = mapfiles.RiverMap(eu4, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, provinceDef)

    print("Recoloring provinces...")
    recolorTerrain = recolor.Recolor(provinceMap, provinceDef)
    for province in provinceMap.provinces:
        if province in defaultMap.seas + defaultMap.lakes:
            recolorTerrain[province] = (68, 107, 163)
        elif province in climate.wastelands:
            recolorTerrain[province] = (94, 94, 94)
        else:
            terrain = terrainDef.getTerrain(province, defaultMap, terrainMap, provinceMap, treeMap, riverMap)
            recolorTerrain[province] = terrain.color
    generatedTerrainMap = recolorTerrain.generate().bitmap

    print("Getting screenshot...")
    screenshotsDir = f"{game.DOCUMENTS_DIRECTORY}/Screenshots"
    screenshots = os.listdir(screenshotsDir)
    screenshots.sort(key=lambda f: os.path.getmtime(f"{screenshotsDir}/{f}"))
    inGameTerrainMap = img.open(f"{screenshotsDir}/{screenshots[-1]}")

    print("Comparing...")
    overlay = chops.subtract_modulo(generatedTerrainMap, inGameTerrainMap)
    errantProvincesMask = img.new("1", overlay.size)
    for band in overlay.split():
        errantProvincesMask = chops.add(errantProvincesMask, band)
    overlay.paste(provinceMap.bitmap, mask=errantProvincesMask)
    # Any provinces still visible in the overlay are now the same color as on the province map

    generatedTerrainMap.show()
    inGameTerrainMap.show()
    overlay.show()
    provinceMap.bitmap.show()

    print("Finding differences...")
    colorCount: list[tuple[int, tuple[int, int, int]]] = overlay.getcolors() # type: ignore

    # Given a province, extract its color from the given terrain map and summarize what terrain it represents
    def assessTerrain(provinceID: int, terrainMap: img.Image) -> str:
        provinceMask = provinceMap.masks[provinceID]
        province = terrainMap.crop(provinceMask.boundingBox)
        province.paste(provinceMask.bitmap, mask=provinceMask.inverted().bitmap)
        colorCount: list[tuple[int, tuple[int, int, int]]] = province.getcolors() # type: ignore
        colors = [c[1] for c in colorCount]
        if len(colors) == 1:
            return "(no color)" # only black
        if len(colors) > 2:
            return "(multiple colors)"
        color = next(filter(lambda c: c != (0, 0, 0), colors)) # filter out black
        possibleTerrains = list(filter(lambda t: t.color == color, terrainDef.terrains))
        if len(possibleTerrains) == 0:
            return f"{color} [unknown terrain]"
        if len(possibleTerrains) > 1:
            return f"{color} [multiple terrains]"
        return f"{color} [{possibleTerrains[0].name}]"

    # Iterate over every province visible in the overlay
    for _, provinceColor in colorCount:
        if provinceColor == (0, 0, 0):
            continue
        provinceID = provinceDef.province.get(provinceColor)
        if provinceID is None:
            continue
        if provinceID in defaultMap.seas + defaultMap.lakes:
            # water provinces may have misconfigured terrain, wrongly appearing white in the screenshot, so ignore them
            continue
        print(f"Province {provinceID} {provinceColor}:")
        print(f"\tGenerated: {assessTerrain(provinceID, generatedTerrainMap)}")
        print(f"\tIn-game: {assessTerrain(provinceID, inGameTerrainMap)}")
