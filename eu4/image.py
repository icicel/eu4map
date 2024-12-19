import itertools
import PIL.Image as img
import PIL.ImageChops as chops


# Generic RGB bitmap object
class Bitmap:
    bitmap: img.Image

    # Loads an image from a file
    def load(self, path: str):
        self.bitmap = img.open(path)

    # Outputs the image to a file
    # Format is PNG to avoid losing transparency information if it exists
    def save(self, path: str):
        self.bitmap.save(path, "PNG")

    # Doubles the size of the image
    def double(self):
        self.bitmap = self.bitmap.resize((self.bitmap.width * 2, self.bitmap.height * 2), img.Resampling.NEAREST)


# Bitmap with three channels
class RGB(Bitmap):
    def __init__(self, image: img.Image):
        if image.mode != "RGB":
            raise ValueError("RGB must be RGB")
        self.bitmap = image


# Bitmap with four channels
class RGBA(Bitmap):
    def __init__(self, image: img.Image):
        if image.mode != "RGBA":
            raise ValueError("RGBA must be RGBA")
        self.bitmap = image

    # Remove the alpha channel
    def asRGB(self) -> RGB:
        return RGB(self.bitmap.convert("RGB"))


# Bitmap with a single channel
class Grayscale(Bitmap):
    def __init__(self, image: img.Image):
        if image.mode != "L":
            raise ValueError("Grayscale must be grayscale")
        self.bitmap = image

    # Map non-black pixels to white (essentially making the image binary)
    def flattened(self) -> "Grayscale":
        return Grayscale(self.bitmap.point(lambda p: 255 if p else 0))
    
    # Invert colors
    def inverted(self) -> "Grayscale":
        return Grayscale(chops.invert(self.bitmap))

    # Converts to an RGB image
    # Basically just copies the image to all three channels
    def asRGB(self) -> RGB:
        return RGB(self.bitmap.convert("RGB"))


class Palette(Bitmap):
    def __init__(self, image: img.Image):
        if image.mode != "P":
            raise ValueError("Palette must be paletted")
        self.bitmap = image

    def paletteRGB(self) -> list[tuple[int, int, int]]:
        palette = self.bitmap.getpalette()
        if not palette:
            return []
        return list(itertools.batched(palette, 3)) # type: ignore

    def usedColors(self) -> set[int]:
        colorCount: list[tuple[int, int]] = self.bitmap.getcolors() # type: ignore
        return set(color for _, color in colorCount)


# Bitmap with a single channel that uses only 1 bit per pixel
# Loaded from raw binary data
class Binary(Bitmap):
    def __init__(self, size: tuple[int, int], data: bytearray):
        self.bitmap = img.frombytes("1", size, data)

    def inverted(self) -> "Binary":
        invertedBytes = bytearray(self.bitmap.point(lambda p: 0 if p else 1).tobytes())
        return Binary(self.bitmap.size, invertedBytes)


# Overlays one image on top of another according to a mask
# White pixels in the mask show the base image, black pixels show the overlay image
def overlay(image: RGB, overlay: RGB, mask: Grayscale) -> RGB:
    return RGB(chops.composite(image.bitmap, overlay.bitmap, mask.bitmap))
