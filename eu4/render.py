import PIL.Image as img
import PIL.ImageDraw as draw

from eu4 import image
from eu4 import mapfiles


# Render all province masks next to each other like a sprite sheet or bitmap font page
def renderMasks(provinces: mapfiles.ProvinceMap) -> image.RGB:
    # sort by height, then by width, largest first
    masks = list(provinces.masks.values())
    masks.sort(key=lambda mask: (mask.mask.bitmap.height, mask.mask.bitmap.width), reverse=True)

    # binary search for the smallest square that fits all masks
    MIN = int(sum(mask.mask.bitmap.width * mask.mask.bitmap.height for mask in masks) ** 0.5)
    MAX = 2 * MIN
    while MIN < MAX:
        size = (MIN + MAX) // 2
        maskmap = _fitMasks(size, masks)
        if maskmap: # fits
            MAX = size
        else: # does not fit
            MIN = size + 1
    
    # the final size might not actually fit, so increment until it does
    while True:
        maskmap = _fitMasks(MIN, masks)
        if maskmap:
            break
        MIN += 1
    return image.RGB(maskmap)

# A pixel where there is a mask above, a mask or border to the left, and nothing below
# New "rows" may start here if the starting mask isn't taller than the ledge's fit
class MaskLedge:
    def __init__(self, x: int, y: int, fit: int, bottomSpace: int):
        self.x: int = x
        self.y: int = y
        self.fit: int = fit
        self.bottomSpace: int = bottomSpace

# Try to fit the map's province masks into a square of the given size
# Masks have padding of 1 pixel on all sides
# Returns None if the masks cannot fit
def _fitMasks(squareSize: int, masks: list[mapfiles.ProvinceMask]) -> img.Image | None:
    square = img.new("RGB", (squareSize, squareSize), (255, 0, 0))
    x: int = 0
    y: int = 0
    ledges: list[MaskLedge] = []

    for mask in masks:
        maskWidth, maskHeight = mask.mask.bitmap.size
        if maskWidth + 2 > squareSize or maskHeight + 2 > squareSize:
            return None
        
        # overflow to the right, start a new row
        if x + maskWidth + 1 > squareSize - 1:
            # go backwards until a fitting ledge is found
            for i, ledge in enumerate(reversed(ledges)):
                if ledge.x + maskWidth + 1 > squareSize - 1: # still overflowing
                    continue
                if maskHeight + 1 > ledge.fit: # starting the row here would create a lip
                    continue
                x, y = ledge.x, ledge.y
                # invalidate passed ledges, including this one
                ledges = ledges[:-i-1]
                break
            # if not even the first ledge fits, then there is no bottom space left
            else:
                # go forwards until a ledge with enough bottom space is found
                for i, ledge in enumerate(ledges):
                    if maskHeight + 1 > ledge.bottomSpace:
                        continue
                    x, y = ledge.x, ledge.y
                    # invalidate all ledges
                    ledges = []
                    break
                # no ledges have enough bottom space - the square is full
                else:
                    return None

        # nudge as far up as possible if not starting a new row
        else:
            while True:
                y -= 1
                # check the top left/right corners of where the actual mask would be, not the padding
                if y < 0 or square.getpixel((x+1, y+1)) != (255, 0, 0) or square.getpixel((x + maskWidth, y+1)) != (255, 0, 0):
                    y += 1
                    break

        # paste the mask with a 1 pixel green padding
        square.paste(mask.mask.bitmap, (x + 1, y + 1))
        draw.Draw(square).rectangle([x, y, x + maskWidth + 1, y + maskHeight + 1], outline=(0, 255, 0))

        # update ledges with the new one formed by this mask and the mask/image border to its left
        ledgeX = x
        ledgeY = y + maskHeight + 1
        bottomDistance = squareSize - 1 - ledgeY
        if ledges:
            heightDifference = ledges[-1].y - ledgeY
            ledges.append(MaskLedge(ledgeX, ledgeY, heightDifference, bottomDistance))
        else: # first mask
            ledges.append(MaskLedge(ledgeX, ledgeY, bottomDistance, bottomDistance))

        # move to the right
        x += maskWidth + 1

    return square
