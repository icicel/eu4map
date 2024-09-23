import eu4map.files as files
import eu4map.bitmap as bitmap

class Game:
    gamefiles: files.Files

    # takes the steam directory (where game files are stored) and documents directory (where mods are stored)
    def __init__(self, steamPath: str, documentsPath: str):
        self.gamefiles = files.Files(steamPath, documentsPath)
    
    def getProvinceMap(self) -> bitmap.ProvinceMap:
        return bitmap.ProvinceMap(self.gamefiles)
