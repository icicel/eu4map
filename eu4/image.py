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


# Adds the bands of multiple images together
def mergeBands(images: list[img.Image]) -> Grayscale:
    result = img.new("L", images[0].size)
    for image in images:
        for band in image.split():
            result = chops.add(result, band)
    return Grayscale(result)
