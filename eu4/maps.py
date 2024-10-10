import PIL.Image as img
import eu4.game as game

# a bitmap where each RGB color represents a province
class ProvinceMap:
    image: img.Image
    def __init__(self, game: game.Game):
        provinces_bmp = game.getFile("map/provinces.bmp")
        self.image = img.open(provinces_bmp)
