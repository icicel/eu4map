import re
import os

from eu4 import game
from eu4 import mapfiles
from eu4 import presets
from eu4 import render

def test(mod: game.Mod):
    name = mod.name.decode("cp1252")
    dirname = re.sub(r"[^a-z0-9]", "_", name.lower())
    if os.path.exists(f"test/{dirname}/output.png"):
        return
    print(f"Loading mod {name}...")
    os.makedirs(f"test/{dirname}", exist_ok=True)
    eu4 = game.Game(mod=mod.path)

    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(eu4)
    definition = mapfiles.ProvinceDefinition(eu4, defaultMap)
    climate = mapfiles.Climate(eu4, defaultMap)
    heightmap = mapfiles.Heightmap(eu4, defaultMap)
    terrain = mapfiles.TerrainMap(eu4, defaultMap)
    terrainDefinition = mapfiles.TerrainDefinition(eu4, defaultMap)

    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, definition)

    presets.blank(defaultMap, provinceMap, definition, climate).save(f"test/{dirname}/output.png")
    presets.landProvinces(defaultMap, provinceMap, definition, climate).save(f"test/{dirname}/output1.png")
    presets.template(defaultMap, provinceMap, definition, climate).save(f"test/{dirname}/output2.png")
    presets.colorableTemplate(defaultMap, provinceMap, definition, climate).save(f"test/{dirname}/output3.png")
    presets.heightmapCoast(defaultMap, provinceMap, definition, heightmap).save(f"test/{dirname}/output4.png")
    presets.simpleTerrain(defaultMap, provinceMap, definition, climate, terrainDefinition, terrain).save(f"test/{dirname}/output5.png")
    render.renderMasks(provinceMap).save(f"test/{dirname}/output0.png")
    render.renderMasksWithTerrain(provinceMap, terrain).save(f"test/{dirname}/output00.png")

print("Finding mods...")
for mod in game.getAllMods(game.DOCUMENTS_DIRECTORY):
    if os.path.exists(f"{mod.path}/map/provinces.bmp"):
        test(mod)
