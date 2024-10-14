import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw
import eu4.game as game


# a bitmap where each RGB color represents a province
class ProvinceMap:
    image: img.Image
    def __init__(self, game: game.Game):
        provinces_bmp = game.getFile("map/provinces.bmp")
        self.image = img.open(provinces_bmp)


# a b&w bitmap where a pixel is black if it's a border pixel and white otherwise
# its mode is "L" (grayscale)
class BorderMap:
    image: img.Image
    def __init__(self, provinces: ProvinceMap):
        # create shift-difference images for each direction
        shiftDown = shiftDifference(provinces.image, 0, 1)
        shiftRight = shiftDifference(provinces.image, 1, 0)
        shiftDownRight = shiftDifference(provinces.image, 1, 1)
        # merge all 9 image bands into one grayscale image
        # the only non-black pixels in the result are the borders
        bands = shiftDown.split() + shiftRight.split() + shiftDownRight.split()
        borders = bands[0]
        for band in bands[1:]:
            borders = chops.add(borders, band)
        # grayscale, then set black to white and non-black to black
        self.image = borders.convert("L").point(lambda p: 0 if p else 255)


# overlay a border image on a province map
def borderOverlay(provinces: ProvinceMap, borders: BorderMap) -> img.Image:
    return img.composite(provinces.image, borders.image.convert("RGB"), borders.image)


# returns pixel difference between an image and itself shifted down-rightwards
# if a pixel is non-black in the difference image, 
# it means its color changed between the original and the shifted image
def shiftDifference(image: img.Image, shiftX: int, shiftY: int) -> img.Image:
    shifted = image.transform(
        image.size, 
        img.Transform.AFFINE, 
        (1, 0, -shiftX, 0, 1, -shiftY))
    diff = chops.difference(image, shifted)
    # set pixels outside the shifted image's range to black
    if shiftX:
        draw.Draw(diff).rectangle((0, 0, shiftX - 1, diff.height), fill=0)
    if shiftY:
        draw.Draw(diff).rectangle((0, 0, diff.width, shiftY - 1), fill=0)
    return diff
