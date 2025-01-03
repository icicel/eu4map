import re
import os

from eu4 import game
from eu4 import mapfiles
from eu4 import presets
from eu4 import render


def testPresets(game: game.Game, outputDir: str):

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(game)
    definition = mapfiles.ProvinceDefinition(game, defaultMap)
    climate = mapfiles.Climate(game, defaultMap)
    heightmap = mapfiles.Heightmap(game, defaultMap)
    terrain = mapfiles.TerrainMap(game, defaultMap)
    terrainDefinition = mapfiles.TerrainDefinition(game, defaultMap)
    tree = mapfiles.TreeMap(game, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(game, defaultMap, definition)

    presets.blank(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output.png")
    presets.landProvinces(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output1.png")
    presets.template(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output2.png")
    presets.colorableTemplate(defaultMap, provinceMap, definition, climate).save(f"{outputDir}/output3.png")
    presets.heightmapCoast(defaultMap, provinceMap, definition, heightmap).save(f"{outputDir}/output4.png")
    presets.simpleTerrain(defaultMap, provinceMap, definition, climate, terrainDefinition, terrain, tree).save(f"{outputDir}/output5.png")
    render.renderTerrainLegend(terrain, terrainDefinition).save(f"{outputDir}/output50.png")
    presets.overridden(defaultMap, provinceMap, definition, climate, terrainDefinition).save(f"{outputDir}/output6.png")
    render.renderMasks(provinceMap).save(f"{outputDir}/output0.png")
    render.renderMasksWithTerrain(provinceMap, terrain).save(f"{outputDir}/output00.png")


def testGame(modloader: bool = False, mod: str | int | list[str | int] | None = None):
    os.makedirs(f"test", exist_ok=True)

    print("Loading game...")
    eu4 = game.Game(modloader, mod)
    testPresets(eu4, f"test")


def testAllMods():
    print("Finding mods...")
    mods = game.getAllMods(game.DOCUMENTS_DIRECTORY)

    for mod in mods:
        if not os.path.exists(f"{mod.path}/map/default.map"):
            # mod doesn't edit the map
            continue
        
        dirname = re.sub(r"[^a-z0-9]+", "_", mod.name.lower())
        if os.path.exists(f"test/{dirname}/output00.png"):
            # already tested the mod
            return
        os.makedirs(f"test/{dirname}", exist_ok=True)
        
        print(f"Loading mod {mod.name}... ({mod.technicalName})")
        eu4 = game.Game(mod=mod.path)
        testPresets(eu4, f"test/{dirname}")
