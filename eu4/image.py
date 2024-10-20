import PIL.Image as img


# Generic bitmap object
class Bitmap:
    bitmap: img.Image
    def __init__(self, path: str):
        self.bitmap = img.open(path)

    # Outputs the image to a file
    def save(self, path: str):
        self.bitmap.save(path)


# Bitmap with a single channel
class Grayscale(Bitmap):
    def __init__(self, path: str):
        super().__init__(path)
