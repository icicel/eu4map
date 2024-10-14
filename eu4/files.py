import PIL.Image as img

# Generic bitmap object
class Bitmap:
    bitmap: img.Image

    # Outputs the image to a file
    def save(self, path: str):
        self.bitmap.save(path)
