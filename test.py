from eu4 import game
from eu4 import presets


eu4 = game.Game(modloader=True)

presets.blank(eu4).save("output.bmp")
presets.landProvinces(eu4).save("output1.bmp")
presets.template(eu4).save("output2.bmp")
presets.colorableTemplate(eu4).save("output3.bmp")
