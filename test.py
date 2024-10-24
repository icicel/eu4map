from eu4 import image
from eu4 import game
from eu4.maps import maps
from eu4.maps import provinces


eu4 = game.Game()
print(eu4.loadOrder)

defaultMap = maps.DefaultMap(eu4)
provinceMap = provinces.ProvinceMap(eu4, defaultMap)

borders = provinces.doubleBorderize(provinceMap)
image.overlay(provinceMap, image.expandToRGB(borders), borders).save("output.bmp")


moddedEu4 = game.Game(modloader=True)
print(moddedEu4.loadOrder)

defaultMap = maps.DefaultMap(moddedEu4)
provinceMapBackground = provinces.ProvinceMap(moddedEu4, defaultMap)
provinceMapBorders = provinces.ProvinceMap(moddedEu4, defaultMap)
definition = maps.ProvinceDefinition(moddedEu4, defaultMap)
climate = maps.Climate(moddedEu4, defaultMap)

seas: list[int] = defaultMap["sea_starts"]
lakes: list[int] = defaultMap["lakes"]
wastelands: list[int] = climate["impassable"]
nonprovinces: list[int] = seas + lakes + wastelands

recolorBackground: dict[int, tuple[int, int, int]] = {}
for sea in defaultMap["sea_starts"]:
    recolorBackground[sea] = (185, 194, 255)
for lake in defaultMap["lakes"]:
    recolorBackground[lake] = (185, 194, 255)
for wasteland in climate["impassable"]:
    recolorBackground[wasteland] = (94, 94, 94)
provinceMapBackground.recolor(recolorBackground, definition, default=(255, 255, 255))

recolorBorders: dict[int, tuple[int, int, int]] = {}
for nonprovince in nonprovinces:
    recolorBorders[nonprovince] = (255, 255, 255)
provinceMapBorders.recolor(recolorBorders, definition)

borders = provinces.borderize(provinceMapBorders)
image.overlay(provinceMapBackground, image.expandToRGB(borders), borders).save("output2.bmp")
