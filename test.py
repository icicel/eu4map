import eu4.game as game

eu4 = game.Game(modloader=True)
print(eu4.gamefiles.loadOrder)

pmap = eu4.getProvinceMap()
pmap.borderize().save("output.bmp")

eu42 = game.Game(mod=3327591954)
print(eu42.gamefiles.loadOrder)
