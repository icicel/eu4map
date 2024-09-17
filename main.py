import os, bitmap, parse

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"

pmap = bitmap.ProvinceMap(os.path.join(GAME_DIRECTORY, "map/provinces.bmp"))
pmap.borderOverlay().save("output.bmp")

print(parse.parse(os.path.join(GAME_DIRECTORY, "history/countries/AAC - Aachen.txt")))
