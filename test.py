from eu4 import image
from eu4 import game
from eu4.maps import maps
from eu4.maps import provinces


eu4 = game.Game()
print(eu4.loadOrder)

defaultMap = maps.DefaultMap(eu4)
pmap = provinces.ProvinceMap(eu4, defaultMap)

borders = provinces.doubleBorderize(pmap)
image.overlay(pmap.bitmap, borders.bitmap.convert("RGB"), borders).save("output.bmp")


moddedEu4 = game.Game(modloader=True)
print(moddedEu4.loadOrder)

defaultMap = maps.DefaultMap(moddedEu4)
pmap = provinces.ProvinceMap(moddedEu4, defaultMap)
definition = maps.ProvinceDefinition(moddedEu4, defaultMap)
climate = maps.Climate(moddedEu4, defaultMap)

recolor: dict[int, tuple[int, int, int]] = {}
for sea in defaultMap["sea_starts"]:
    recolor[sea] = (185, 194, 255)
for lake in defaultMap["lakes"]:
    recolor[lake] = (185, 194, 255)
for wasteland in climate["impassable"]:
    recolor[wasteland] = (94, 94, 94)
pmap.recolor(recolor, definition)

borders = provinces.borderize(pmap)
image.overlay(pmap.bitmap, borders.bitmap.convert("RGB"), borders).save("output2.bmp")
