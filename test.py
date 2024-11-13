from eu4 import game
from eu4 import mapfiles
from eu4 import presets


print("Loading game...")
eu4 = game.Game(modloader=True)

print("Loading data...")
defaultMap = mapfiles.DefaultMap(eu4)
definition = mapfiles.ProvinceDefinition(eu4, defaultMap)
climate = mapfiles.Climate(eu4, defaultMap)
heightmap = mapfiles.Heightmap(eu4, defaultMap)
terrain = mapfiles.TerrainMap(eu4, defaultMap)
terrainDefinition = mapfiles.TerrainDefinition(eu4, defaultMap)

print("Loading map...")
provinceMap = mapfiles.ProvinceMap(eu4, defaultMap, definition)

presets.blank(defaultMap, provinceMap, definition, climate).save("output.png")
presets.landProvinces(defaultMap, provinceMap, definition, climate).save("output1.png")
presets.template(defaultMap, provinceMap, definition, climate).save("output2.png")
presets.colorableTemplate(defaultMap, provinceMap, definition, climate).save("output3.png")
presets.heightmapCoast(defaultMap, provinceMap, definition, heightmap).save("output4.png")
presets.simpleTerrain(defaultMap, provinceMap, definition, climate, terrainDefinition, terrain).save("output5.png")
presets.maskmap(provinceMap).save("output0.png")
