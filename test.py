import os
import eu4map.game as game

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"
DOCUMENTS_DIRECTORY = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis IV")

eu4 = game.Game(GAME_DIRECTORY, DOCUMENTS_DIRECTORY)
print(eu4.files.modPaths)

pmap = eu4.getProvinceMap()
pmap.borderize().save("output.bmp")
