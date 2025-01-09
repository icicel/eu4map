import random
import re
import os
import PIL.Image as img

from eu4 import game
from eu4 import image
from eu4 import mapfiles
from eu4 import presets
from eu4 import recolor
from eu4 import render


def generatePresets(outputDir: str, modloader: bool = False, mod: str | int | list[str | int] | None = None):

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
    print("Finding mods...")
    mods = game.getAllMods(game.DOCUMENTS_DIRECTORY)

    for mod in mods:
        if not os.path.exists(f"{mod.path}/map/default.map"):
            # mod doesn't edit the map
            continue
        
        dirname = re.sub(r"^_+|_+$", "", re.sub(r"[^a-z0-9.']+", "_", mod.name.lower()))
        if os.path.exists(f"test/{dirname}/output00.png"):
            # already tested the mod
            return
        os.makedirs(f"test/{dirname}", exist_ok=True)
        
        print(f"*** Testing mod {mod.name} ({mod.technicalName})")
        generatePresets(f"test/{dirname}", mod=mod.path)


def generateTerrainTest(modloader: bool = False, mod: str | int | list[str | int] | None = None):

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
