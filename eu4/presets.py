from eu4 import image
from eu4 import game
from eu4.maps import maps
from eu4.maps import provinces


# Simply colors water, wastelands and land provinces in different colors
def blank(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = maps.DefaultMap(game)
    definition = maps.ProvinceDefinition(game, defaultMap)
    climate = maps.Climate(game, defaultMap)
    provinceMap = provinces.ProvinceMap(game, defaultMap)

    print("Recoloring...")
    recolor: dict[int, tuple[int, int, int]] = {}
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolor[water] = (68, 107, 163)
    for wasteland in climate["impassable"]:
        recolor[wasteland] = (94, 94, 94)
    provinceMap.recolor(recolor, definition, default=(150, 150, 150))

    print("Done!")
    return provinceMap


# Colors non-land provinces black
# Land provinces are left with their original colors
def landProvinces(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = maps.DefaultMap(game)
    definition = maps.ProvinceDefinition(game, defaultMap)
    climate = maps.Climate(game, defaultMap)
    provinceMap = provinces.ProvinceMap(game, defaultMap)

    print("Recoloring...")
    recolor: dict[int, tuple[int, int, int]] = {}
    for nonprovince in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolor[nonprovince] = (0, 0, 0)
    provinceMap.recolor(recolor, definition)

    print("Done!")
    return provinceMap


# Colors water and wastelands
# Land provinces are colored white and have borders
def template(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = maps.DefaultMap(game)
    definition = maps.ProvinceDefinition(game, defaultMap)
    climate = maps.Climate(game, defaultMap)
    backgroundMap = provinces.ProvinceMap(game, defaultMap)
    borderMap = provinces.ProvinceMap(game, defaultMap)
    
    print("Recoloring...")
    recolorBackground: dict[int, tuple[int, int, int]] = {}
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate["impassable"]:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap.recolor(recolorBackground, definition, default=(255, 255, 255))

    print("Generating borders...")
    recolorBorders: dict[int, tuple[int, int, int]] = {}
    for nonland in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolorBorders[nonland] = (255, 255, 255)
    borderMap.recolor(recolorBorders, definition)
    borders = provinces.borderize(borderMap)

    print("Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)


# Like template, but land provinces are colored in different shades of white
def colorableTemplate(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = maps.DefaultMap(game)
    definition = maps.ProvinceDefinition(game, defaultMap)
    climate = maps.Climate(game, defaultMap)
    backgroundMap = provinces.ProvinceMap(game, defaultMap)
    borderMap = provinces.ProvinceMap(game, defaultMap)
    
    print("Recoloring...")
    recolorBackground: dict[int, tuple[int, int, int]] = {}
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate["impassable"]:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap.recolor(recolorBackground, definition, default=provinces.SpecialColor.SHADES_OF_WHITE)

    print("Generating borders...")
    recolorBorders: dict[int, tuple[int, int, int]] = {}
    for nonprovince in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolorBorders[nonprovince] = (255, 255, 255)
    borderMap.recolor(recolorBorders, definition)
    borders = provinces.borderize(borderMap)

    print("Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)
