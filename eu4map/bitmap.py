import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw
import eu4map.files as files

# a bitmap where each RGB color represents a province
class ProvinceMap:
    image: img.Image
    def __init__(self, files: files.Files):
        provinces_bmp = files.getFile("map/provinces.bmp")
        self.image = img.open(provinces_bmp)

    # create a b&w border image from the province map
    # its mode is "L" (grayscale)
    def borderize(self) -> img.Image:
        # create shift-difference images for each direction
        shiftDown = self.shiftDifference(0, 1)
        shiftRight = self.shiftDifference(1, 0)
        shiftDownRight = self.shiftDifference(1, 1)
        # merge all 9 image bands into one grayscale image
        # the only non-black pixels in the result are the borders
        bands = shiftDown.split() + shiftRight.split() + shiftDownRight.split()
        borders = bands[0]
        for band in bands[1:]:
            borders = chops.add(borders, band)
        # grayscale, then set black to white and non-black to black
        return borders.convert("L").point(lambda p: 0 if p else 255)
    
    # create and overlay a border image on the province map
    def borderOverlay(self) -> img.Image:
        borders = self.borderize()
        return img.composite(self.image, borders.convert("RGB"), borders)

    # returns pixel difference between the map and itself shifted down-rightwards
    # if a pixel is non-black in the difference image, 
    # it means its color changed between the original and the shifted image
    def shiftDifference(self, shiftX: int, shiftY: int) -> img.Image:
        shifted = self.image.copy().transform(
            self.image.size, 
            img.Transform.AFFINE, 
            (1, 0, -shiftX, 0, 1, -shiftY))
        diff = chops.difference(self.image, shifted)
        # set pixels outside the shifted image's range to black
        if shiftX:
            draw.Draw(diff).rectangle((0, 0, shiftX - 1, diff.height), fill=0)
        if shiftY:
            draw.Draw(diff).rectangle((0, 0, diff.width, shiftY - 1), fill=0)
        return diff
