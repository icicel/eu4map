from eu4 import game
from eu4.maps import maps
from eu4.maps import provinces

eu4 = game.Game(modloader=True)
print(eu4.loadOrder)

defaultMap = maps.DefaultMap(eu4)
pmap = provinces.ProvinceMap(eu4, defaultMap)
provinces.BorderMap(pmap).save("output.bmp")

eu42 = game.Game(mod=[3327591954, 2783633869])
print(eu42.loadOrder)

defaultMap = maps.DefaultMap(eu42)
pmap = provinces.ProvinceMap(eu42, defaultMap)
provinces.BorderMap(pmap).save("output2.bmp")
