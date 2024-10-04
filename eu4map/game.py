import eu4map.files as files
import eu4map.bitmap as bitmap

class Game:
    gamefiles: files.Files

    # takes the steam directory (where game files are stored) and documents directory (where mods are stored)
    def __init__(self, steamPath: str, documentsPath: str | None = None, modPaths: list[str] | None = None):
        self.gamefiles = files.Files(steamPath, documentsPath, modPaths)
    
    def getProvinceMap(self) -> bitmap.ProvinceMap:
        return bitmap.ProvinceMap(self.gamefiles)
