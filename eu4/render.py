import PIL.Image as img
import PIL.ImageDraw as draw

from eu4 import image
from eu4 import mapfiles


# Render all province masks next to each other like a sprite sheet or bitmap font page
def renderMasks(provinces: mapfiles.ProvinceMap) -> image.RGB:
    # sort by height, then by width
    # this will not affect the ProvinceMap object
    provinces.masks.sort(key=lambda mask: (mask.mask.bitmap.height, mask.mask.bitmap.width), reverse=True)

    # start with the smallest possible square
    SIZE = int(sum(mask.mask.bitmap.width * mask.mask.bitmap.height for mask in provinces.masks) ** 0.5)

    while True:
        maskmap = _fitMasks(SIZE, provinces)
        if maskmap:
            return image.RGB(maskmap)
        SIZE += 50

def _tooWide(x: int, width: int, size: int) -> bool:
    return x + width + 2 > size
def _tooTall(y: int, height: int, size: int) -> bool:
    return y + height + 2 > size

# Try to fit the map's province masks into a square of the given size
# Returns None if the masks cannot fit
def _fitMasks(squareSize: int, provinces: mapfiles.ProvinceMap) -> img.Image | None:
    square = img.new("RGB", (squareSize, squareSize), (255, 0, 0))
    x: int = squareSize # start as squareSize to force a new row on the first mask
    y: int = 0
    nextRowX: int = 0
    nextRowY: int = 0
    for mask in provinces.masks:
        maskWidth, maskHeight = mask.mask.bitmap.size
        if maskWidth > squareSize or maskHeight > squareSize:
            return None
        if _tooWide(x, maskWidth, squareSize):
            # move to the next row
            x = nextRowX
            y = nextRowY
            nextRowY += maskHeight + 2
            if _tooTall(y, maskHeight, squareSize):
                # nudge row to the right
                while _tooTall(y, maskHeight, squareSize):
                    x += 1
                    if _tooWide(x, maskWidth, squareSize):
                        return None
                    while True:
                        y -= 1
                        if y < 0 or square.getpixel((x, y)) != (255, 0, 0) or square.getpixel((x + maskWidth + 1, y)) != (255, 0, 0):
                            y += 1
                            break
                nextRowX = x
                nextRowY = y + maskHeight + 2
        else:
            while True:
                y -= 1
                if y < 0 or square.getpixel((x, y)) != (255, 0, 0) or square.getpixel((x + maskWidth + 1, y)) != (255, 0, 0):
                    y += 1
                    break
        # paste the mask with a 1 pixel green border
        square.paste(mask.mask.bitmap, (x + 1, y + 1))
        draw.Draw(square).rectangle([x, y, x + maskWidth + 1, y + maskHeight + 1], outline=(0, 255, 0))
        # move to the right
        x += maskWidth + 2
    return square
