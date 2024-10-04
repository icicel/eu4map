import os
import eu4map.game as game

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"
DOCUMENTS_DIRECTORY = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis IV")
MOD_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/3327591954"

eu4 = game.Game(GAME_DIRECTORY, documentsPath=DOCUMENTS_DIRECTORY)
print(eu4.gamefiles.loadOrder)

pmap = eu4.getProvinceMap()
pmap.borderize().save("output.bmp")

eu42 = game.Game(GAME_DIRECTORY, modPaths=[MOD_DIRECTORY])
print(eu42.gamefiles.loadOrder)
