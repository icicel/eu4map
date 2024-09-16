import PIL.Image as img
import PIL.ImageChops as chops

class ProvinceMap:
    image: img.Image
    def __init__(self, file: str):
        # add an alpha channel for compositing
        self.image = img.open(file).convert("RGBA")

    # create a b&w border image from the province map
    def borderize(self) -> img.Image:
        # create shift-difference images for each direction
        shiftDown = self.shiftDifference(0, -1)
        shiftRight = self.shiftDifference(-1, 0)
        shiftDownRight = self.shiftDifference(-1, -1)
        # merge all 9 image bands into one grayscale image
        bands = shiftDown.split() + shiftRight.split() + shiftDownRight.split()
        borders = bands[0]
        for band in bands[1:]:
            borders = chops.add(borders, band)
        # set black to white and non-black to black
        return borders.point(lambda p: 0 if p else 255)

    # returns pixel difference between the map and a shifted version of itself
    def shiftDifference(self, shiftX: int, shiftY: int) -> img.Image:
        shifted = self.image.copy().transform(
            self.image.size, 
            img.Transform.AFFINE, 
            (1, 0, shiftX, 0, 1, shiftY),
            fillcolor=(0, 0, 0, 0)) # transparent black
        # fill outside the transform with the original image
        shifted = img.alpha_composite(self.image, shifted)
        # difference with original image
        return chops.difference(self.image, shifted)
