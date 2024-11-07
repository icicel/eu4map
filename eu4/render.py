import PIL.Image as img
import PIL.ImageDraw as draw

from eu4 import image
from eu4 import mapfiles


# Render all province masks next to each other like a sprite sheet or bitmap font page
def renderMasks(provinces: mapfiles.ProvinceMap) -> image.RGB:
    # sort by height, then by width
    # this will not affect the ProvinceMap object
    provinces.masks.sort(key=lambda mask: (mask.mask.bitmap.height, mask.mask.bitmap.width), reverse=True)

    # start with this width and height
    SIZE = 6000

    maskmap = fitMasks(SIZE, provinces)
    if not maskmap:
        raise Exception("Failed to fit masks into a square")    
    return image.RGB(maskmap)


# Try to fit the map's province masks into a square of the given size
# Returns None if the masks cannot fit
def fitMasks(squareSize: int, provinces: mapfiles.ProvinceMap) -> img.Image | None:
    square = img.new("RGB", (squareSize, squareSize), (255, 0, 0))
    x: int = squareSize # start as squareSize to force a new row on the first mask
    y: int = 0
    nextHeight = 0
    for mask in provinces.masks:
        maskWidth, maskHeight = mask.mask.bitmap.size
        # create new row if too wide
        if x + maskWidth + 2 >= squareSize:
            x = 0
            y = nextHeight
            nextHeight += maskHeight + 2
            # abort if still too wide
            if x + maskWidth + 2 >= squareSize:
                return None
        # move the mask up as much as possible
        while y >= 0 and square.getpixel((x, y)) == (255, 0, 0) and square.getpixel((x + maskWidth + 1, y)) == (255, 0, 0):
            y -= 1
        y += 1
        # paste the mask with a 1 pixel green border
        square.paste(mask.mask.bitmap, (x + 1, y + 1))
        draw.Draw(square).rectangle([x, y, x + maskWidth + 1, y + maskHeight + 1], outline=(0, 255, 0))
        # move to the right
        x += maskWidth + 2
    return square
