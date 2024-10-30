from eu4 import game
from eu4 import image
from eu4 import mapfiles
from eu4 import recolor
from eu4 import render


# Simply colors water, wastelands and land provinces in different colors
def blank(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(game)
    definition = mapfiles.ProvinceDefinition(game, defaultMap)
    climate = mapfiles.Climate(game, defaultMap)
    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(game, defaultMap)

    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolorBackground[water] = (68, 107, 163)
    for wasteland in climate["impassable"]:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=(150, 150, 150))

    print("Done!")
    return backgroundMap


# Colors non-land provinces black
# Land provinces are left with their original colors
def landProvinces(game: game.Game) -> image.RGBA:
    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(game)
    definition = mapfiles.ProvinceDefinition(game, defaultMap)
    climate = mapfiles.Climate(game, defaultMap)
    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(game, defaultMap)

    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for nonprovince in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolorBackground[nonprovince] = recolor.SpecialColor.TRANSPARENT
    backgroundMap = recolorBackground.generateWithAlpha()

    print("Done!")
    return backgroundMap


# Colors water and wastelands
# Land provinces are colored white and have borders
def template(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(game)
    definition = mapfiles.ProvinceDefinition(game, defaultMap)
    climate = mapfiles.Climate(game, defaultMap)
    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(game, defaultMap)
    
    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate["impassable"]:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=(255, 255, 255))

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonland in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolorBorders[nonland] = (255, 255, 255)
    borderMap = recolorBorders.generate()
    borders = render.renderBorders(borderMap)

    print("Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)


# Like template, but land provinces are colored in different shades of white
def colorableTemplate(game: game.Game) -> image.RGB:
    print("Loading data...")
    defaultMap = mapfiles.DefaultMap(game)
    definition = mapfiles.ProvinceDefinition(game, defaultMap)
    climate = mapfiles.Climate(game, defaultMap)
    print("Loading map...")
    provinceMap = mapfiles.ProvinceMap(game, defaultMap)
    
    print("Recoloring...")
    recolorBackground = recolor.Recolor(provinceMap, definition)
    for water in defaultMap["sea_starts"] + defaultMap["lakes"]:
        recolorBackground[water] = (185, 194, 255)
    for wasteland in climate["impassable"]:
        recolorBackground[wasteland] = (94, 94, 94)
    backgroundMap = recolorBackground.generate(default=recolor.SpecialColor.SHADES_OF_WHITE)

    print("Generating borders...")
    recolorBorders = recolor.Recolor(provinceMap, definition)
    for nonprovince in defaultMap["sea_starts"] + defaultMap["lakes"] + climate["impassable"]:
        recolorBorders[nonprovince] = (255, 255, 255)
    borderMap = recolorBorders.generate()
    borders = render.renderBorders(borderMap)

    print("Done!")
    return image.overlay(backgroundMap, borders.asRGB(), borders)
