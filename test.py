from eu4 import game
from eu4.maps import default
from eu4.maps import provinces

eu4 = game.Game(modloader=True)
print(eu4.loadOrder)

default_map = default.DefaultMap(eu4)
pmap = provinces.ProvinceMap(eu4, default_map)
provinces.BorderMap(pmap).save("output.bmp")

eu42 = game.Game(mod=3327591954)
print(eu42.loadOrder)
