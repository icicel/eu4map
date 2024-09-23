import eu4map.gamefiles as gamefiles
import eu4map.bitmap as bitmap

class Game:
    files: gamefiles.Gamefiles

    # takes the steam directory (where game files are stored) and documents directory (where mods are stored)
    def __init__(self, steamPath: str, documentsPath: str):
        self.files = gamefiles.Gamefiles(steamPath, documentsPath)
    
    def getProvinceMap(self) -> bitmap.ProvinceMap:
        return bitmap.ProvinceMap(self.files.provinces_bmp())
