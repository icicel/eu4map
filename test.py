import eu4map.game as game

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"

eu4 = game.Game(GAME_DIRECTORY)

pmap = eu4.getProvinceMap()
pmap.borderize().save("output.bmp")
