from eu4 import game
from eu4 import presets


eu4 = game.Game(modloader=True)

presets.blank(eu4).save("output.png")
presets.landProvinces(eu4).save("output1.png")
presets.template(eu4).save("output2.png")
presets.colorableTemplate(eu4).save("output3.png")
