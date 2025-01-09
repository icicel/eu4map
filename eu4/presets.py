from eu4 import image
from eu4 import mapfiles
from eu4 import recolor


# Simply colors water, wastelands and land provinces in different colors
def blank(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition, 
        climate: mapfiles.Climate
    ) -> image.RGB:

    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap.seas + defaultMap.lakes:
        recolorBackground[water] = (68, 107, 163)
    for wasteland in climate.wastelands:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=(150, 150, 150))

    print("*** Done!")
    return backgroundMap


# Colors non-land provinces black
# Land provinces are left with their original colors
def landProvinces(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition, 
        climate: mapfiles.Climate
    ) -> image.RGBA:

    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for nonprovince in defaultMap.seas + defaultMap.lakes + climate.wastelands:
        recolorBackground[nonprovince] = recolor.SpecialColor.TRANSPARENT
    backgroundMap = recolorBackground.generateWithAlpha()

    print("*** Done!")
    return backgroundMap


# Colors water and wastelands
# Land provinces are colored white and have borders
def template(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition, 
        climate: mapfiles.Climate
    ) -> image.RGB:
    
    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap.seas + defaultMap.lakes:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate.wastelands:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=(255, 255, 255))

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonland in defaultMap.seas + defaultMap.lakes + climate.wastelands:
        recolorBorders[nonland] = (0, 0, 0)
    borders = recolorBorders.generateBorders()

    print("*** Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)


# Like template, but land provinces are colored in different shades of white
def colorableTemplate(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition, 
        climate: mapfiles.Climate
    ) -> image.RGB:
    
    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap.seas + defaultMap.lakes:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate.wastelands:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=recolor.SpecialColor.SHADES_OF_WHITE)

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonprovince in defaultMap.seas + defaultMap.lakes + climate.wastelands:
        recolorBorders[nonprovince] = (0, 0, 0)
    borders = recolorBorders.generateBorders()

    print("*** Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)


# Generate thin white coastline on the heightmap
def heightmapCoast(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition,
        heightmap: mapfiles.Heightmap
    ) -> image.RGB:

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    # if a water province is not listed as water, then that is literally not my problem
    waters: list[int] = defaultMap.seas + defaultMap.lakes
    for water in waters:
        recolorBorders[water] = (1, 0, 0)
    borders = recolorBorders.generateDoubleBorders(default=(0, 0, 1), filterProvinces=waters)

    print("*** Done!")
    return image.overlay(heightmap.asRGB(), borders.inverted().asRGB(), borders)


def simpleTerrain(
        defaultMap: mapfiles.DefaultMap, 
        provinceMap: mapfiles.ProvinceMap, 
        definition: mapfiles.ProvinceDefinition,
        climate: mapfiles.Climate,
        terrainDefinition: mapfiles.TerrainDefinition,
        terrainMap: mapfiles.TerrainMap,
        treeMap: mapfiles.TreeMap,
        riverMap: mapfiles.RiverMap
    ) -> image.RGB:

    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    waters: set[int] = set(defaultMap.seas + defaultMap.lakes)
    wastelands: set[int] = set(climate.wastelands)
    for province in provinceMap.provinces:
        if province in waters:
            recolorBackground[province] = (185, 194, 255)
        elif province in wastelands:
            recolorBackground[province] = (94, 94, 94)
        else:
            terrain = terrainDefinition.getTerrain(province, defaultMap, terrainMap, provinceMap, treeMap, riverMap)
            recolorBackground[province] = terrain.color
    backgroundMap = recolorBackground.generate()

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonland in defaultMap.seas + defaultMap.lakes + climate.wastelands:
        recolorBorders[nonland] = (0, 0, 0)
    borders = recolorBorders.generateBorders()

    print("*** Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)
