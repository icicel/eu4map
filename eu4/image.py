import PIL.Image as img
import PIL.ImageChops as chops


# Generic RGB bitmap object
class Bitmap:
    bitmap: img.Image
    def __init__(self, path: str):
        self.bitmap = img.open(path)

    # Outputs the image to a file
    def save(self, path: str):
        self.bitmap.save(path)


# Bitmap with a single channel
class Grayscale(Bitmap):
    def __init__(self, image: img.Image):
        if image.mode != "L":
            raise ValueError("Grayscale must be grayscale")
        self.bitmap = image

    # Map non-black pixels to white (essentially making the image binary)
    def flatten(self):
        self.bitmap = self.bitmap.point(lambda p: 255 if p else 0)
    
    # Invert colors
    def invert(self):
        self.bitmap = chops.invert(self.bitmap)


# Overlays one image on top of another according to a mask
# White pixels in the mask show the base image, black pixels show the overlay image
def overlay(image: img.Image, overlay: img.Image, mask: Grayscale) -> img.Image:
    return chops.composite(image, overlay, mask.bitmap)


# Adds the bands of multiple images together into one channel
def mergeBands(images: list[img.Image]) -> Grayscale:
    result = img.new("L", images[0].size)
    for image in images:
        for band in image.split():
            result = chops.add(result, band)
    return Grayscale(result)
