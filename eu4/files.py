import PIL.Image as img
import eu4.parse as parse


# Generic scope file object
class File:
    scope: parse.Scope


# Generic bitmap object
class Bitmap:
    bitmap: img.Image

    # Outputs the image to a file
    def save(self, path: str):
        self.bitmap.save(path)
