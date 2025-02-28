import PIL.Image as img
import PIL.ImageChops as chops
import PIL.ImageDraw as draw
import PIL.ImageFont as font

from eu4 import image
from eu4 import mapfiles
from typing import Callable


# Render all province masks next to each other like a sprite sheet or bitmap font page
def renderMasks(provinces: mapfiles.ProvinceMap) -> image.RGB:
    def placer(maskmap: img.Image, mask: mapfiles.ProvinceMask, x: int, y: int):
        maskmap.paste(mask.bitmap, (x, y))
    return _minimizeMaskmap(provinces, placer)

# Render as above, but with terrain
def renderMasksWithTerrain(provinces: mapfiles.ProvinceMap, terrainMap: mapfiles.TerrainMap) -> image.RGB:
    def placer(maskmap: img.Image, mask: mapfiles.ProvinceMask, x: int, y: int):
        terrainCutout = terrainMap.bitmap.crop(mask.boundingBox)
        maskmap.paste(mask.bitmap, (x, y))
        maskmap.paste(terrainCutout, (x, y), mask.bitmap)
    return _minimizeMaskmap(provinces, placer)

def _minimizeMaskmap(
        provinces: mapfiles.ProvinceMap,
        placer: Callable[[img.Image, mapfiles.ProvinceMask, int, int], None]
    ) -> image.RGB:

    # sort by height, then by width, largest first
    masks = list(provinces.masks.values())
    masks.sort(key=lambda mask: (mask.bitmap.height, mask.bitmap.width), reverse=True)

    # binary search for the smallest square that fits all masks
    minSize = int(sum(mask.bitmap.width * mask.bitmap.height for mask in masks) ** 0.5)
    maxSize = 2 * minSize
    while minSize < maxSize:
        size = (minSize + maxSize) // 2
        maskmap = _fitMasks(size, masks, placer)
        if maskmap: # fits
            maxSize = size
        else: # does not fit
            minSize = size + 1
    
    # the final size might not actually fit, so increment until it does
    while True:
        maskmap = _fitMasks(minSize, masks, placer)
        if maskmap:
            break
        minSize += 1
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
def _fitMasks(
        squareSize: int, 
        masks: list[mapfiles.ProvinceMask],
        placeMask: Callable[[img.Image, mapfiles.ProvinceMask, int, int], None]
    ) -> img.Image | None:

    square = img.new("RGB", (squareSize, squareSize), (255, 0, 0))
    x: int = 0
    y: int = 0
    ledges: list[MaskLedge] = []

    for mask in masks:
        maskWidth, maskHeight = mask.bitmap.size
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
        placeMask(square, mask, x + 1, y + 1)
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


# Render a legend for the simple terrain preset
# TODO: use localized terrain names
def renderTerrainLegend(terrainMap: mapfiles.TerrainMap, terrainDefinition: mapfiles.TerrainDefinition, treeMap: mapfiles.TreeMap) -> image.RGB:
    legendFont = font.load_default()
    pad = 5

    usedTerrains: set[mapfiles.Terrain] = set()
    # Add all terrains that are mapped to by the terrain and tree maps
    for index, _ in terrainMap.usedColors():
        if index not in terrainDefinition.terrainIndex:
            continue
        terrain = terrainDefinition.terrainIndex[index]
        usedTerrains.add(terrain)
    for index, _ in treeMap.usedColors():
        if index not in terrainDefinition.treeIndex:
            continue
        terrain = terrainDefinition.treeIndex[index]
        usedTerrains.add(terrain)
    # Add all terrains that have any overrides and remove water terrains
    for terrain in terrainDefinition.terrains:
        if terrain.overrides:
            usedTerrains.add(terrain)
        if terrain.isWater:
            usedTerrains.discard(terrain)
    # Sort by terrainDefinition order
    terrains = [terrain for terrain in terrainDefinition.terrains if terrain in usedTerrains]

    # Calculate legend dimensions
    _, top, _, bottom = legendFont.getbbox("abcdefghijklmnopqrstuvwxyz0123456789_-")
    rowHeight = int(bottom - top + pad*2)
    rowCount = len(terrains)
    legendHeight = rowCount * rowHeight
    legendWidth = 1000 # unnecessarily long, cut off excess
    legend = img.new("RGB", (legendWidth, legendHeight), (255, 255, 255))

    verticalOffset = 0
    maxWidth = 0
    for terrain in terrains:
        r, g, b = terrain.color
        # https://stackoverflow.com/questions/3942878/how-to-decide-font-color-in-white-or-black-depending-on-background-color
        if (r*0.299 + g*0.587 + b*0.114) > 145:
            fontColor = (0, 0, 0)
        else:
            fontColor = (255, 255, 255)
        draw.Draw(legend).rectangle(xy=[(0, verticalOffset), (legendWidth, verticalOffset + rowHeight)], fill=terrain.color)
        draw.Draw(legend).text(xy=(pad, verticalOffset + pad), text=terrain.name, fill=fontColor, font=legendFont)
        maxWidth = max(maxWidth, legendFont.getlength(terrain.name))
        verticalOffset += rowHeight
    
    return image.RGB(legend.crop((0, 0, maxWidth + pad*2, legendHeight)))


def renderBorders(provinces: image.RGB) -> image.Grayscale:
    '''
    Creates borders between same-colored regions (provinces). Since these are single borders,
    border pixels are effectively only placed on the north and west sides of a province. This
    makes it unsuitable for filtering, unlike `renderDoubleBorders`.

    :param provinces: The image to render borders using
    :return: The border image. A pixel is black if it's a border pixel and white otherwise
    '''
    shiftDown = _shiftDifference(provinces, 0, 1)
    shiftRight = _shiftDifference(provinces, 1, 0)
    shiftDownRight = _shiftDifference(provinces, 1, 1)
    differences = [shiftDown, shiftRight, shiftDownRight]
    return _differencesToBorders(differences)

def renderDoubleBorders(provinces: image.RGB, thick: bool = False) -> image.Grayscale:
    '''
    Creates borders between same-colored regions (provinces). Since these are double borders,
    border pixels are placed on all sides of a province. This means that if you filter certain
    colors to not be able to be borders, other borders will remain unbroken.

    :param provinces: The image to render borders using
    :param thick: Whether the borders should be doubled in width
    :return: The border image. A pixel is black if it's a border pixel and white otherwise
    '''
    shiftDown = _shiftDifference(provinces, 0, 1)
    shiftRight = _shiftDifference(provinces, 1, 0)
    shiftUp = _shiftDifference(provinces, 0, -1)
    shiftLeft = _shiftDifference(provinces, -1, 0)
    differences = [shiftDown, shiftRight, shiftUp, shiftLeft]
    if thick:
        shiftDownRight = _shiftDifference(provinces, 1, 1)
        shiftDownLeft = _shiftDifference(provinces, -1, 1)
        shiftUpRight = _shiftDifference(provinces, 1, -1)
        shiftUpLeft = _shiftDifference(provinces, -1, -1)
        differences += [shiftDownRight, shiftDownLeft, shiftUpRight, shiftUpLeft]
    return _differencesToBorders(differences)

def _differencesToBorders(images: list[img.Image]) -> image.Grayscale:
    '''
    Merge multiple pixel difference images into a single grayscale border image. This is done by
    merging all bands of the input images together, then inverting the result. Thus, black
    pixels in the resulting image mean that the pixel was non-black in at least one
    of the input images.

    :param images: The pixel difference images to merge
    :return: The border image
    '''
    result = img.new("L", images[0].size)
    for im in images:
        for band in im.split():
            result = chops.add(result, band)
    # merge all image bands into one grayscale image
    # the only non-black pixels in the result are the borders
    borders = image.Grayscale(result)
    # set black to white and non-black to black
    return borders.flattened().inverted()

def _shiftDifference(provinces: image.RGB, shiftX: int, shiftY: int) -> img.Image:
    '''
    Returns the pixel difference between an image and a copy of itself shifted down-rightwards
    by the given amount. If a pixel is non-black in the difference image, it means its color
    changed between the original and the shifted image.

    :param provinces: The image to compare
    :param shiftX: The horizontal shift amount (positive is right)
    :param shiftY: The vertical shift amount (positive is down)
    '''
    image = provinces.bitmap
    shifted = image.transform(
        image.size, 
        img.Transform.AFFINE, 
        (1, 0, -shiftX, 0, 1, -shiftY))
    diff = chops.difference(image, shifted)
    # set pixels outside the shifted image's range to black
    drawing = draw.Draw(diff)
    if shiftX > 0:
        drawing.rectangle((0, 0, shiftX - 1, diff.height), fill=0)
    if shiftY > 0:
        drawing.rectangle((0, 0, diff.width, shiftY - 1), fill=0)
    if shiftX < 0:
        drawing.rectangle((diff.width + shiftX, 0, diff.width, diff.height), fill=0)
    if shiftY < 0:
        drawing.rectangle((0, diff.height + shiftY, diff.width, diff.height), fill=0)
    return diff
