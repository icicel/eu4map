import PIL.Image as img
import eu4.parse as parse


# Generic scope file object
class File:
    scope: parse.Scope

    def load(self, path: str) -> None:
        self.scope = parse.parse(path)


# Generic bitmap object
class Bitmap:
    bitmap: img.Image

    def load(self, path: str) -> None:
        self.bitmap = img.open(path)

    # Outputs the image to a file
    def save(self, path: str):
        self.bitmap.save(path)
