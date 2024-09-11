import os, bitmap

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"

pmap = bitmap.ProvinceMap(os.path.join(GAME_DIRECTORY, "map/provinces.bmp"))
pmap.borderize().save("output.bmp")
