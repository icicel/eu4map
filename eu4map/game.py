import os
import eu4map.files as files
import eu4map.bitmap as bitmap

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"
DOCUMENTS_DIRECTORY = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis IV")
WORKSHOP_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/workshop/content/236850"

class Game:
    gamefiles: files.Files

    # Specify modloader=True to load ALL currently active mods from dlc_load.json
    # Specify mod to load a specific mod or list of mods,
    #   either directly by mod directory path (str) or by workshop ID (int)
    def __init__(self, modloader: bool = False, mod: str | int | list[str | int] | None = None):
        gamePath = GAME_DIRECTORY
        documentsPath = DOCUMENTS_DIRECTORY if modloader else None
        modPaths = []
        if isinstance(mod, list):
            for m in mod:
                if isinstance(m, int):
                    modPaths.append(os.path.join(WORKSHOP_DIRECTORY, str(m)))
                elif m:
                    modPaths.append(m)
        elif isinstance(mod, int):
            modPaths.append(os.path.join(WORKSHOP_DIRECTORY, str(mod)))
        elif mod:
            modPaths.append(mod)
        self.gamefiles = files.Files(gamePath, documentsPath, modPaths)
    
    def getProvinceMap(self) -> bitmap.ProvinceMap:
        return bitmap.ProvinceMap(self.gamefiles)
