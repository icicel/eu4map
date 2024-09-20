import json
import os
import eu4map.parse as parse
import eu4map.provincemap as provincemap

# Represents an EU4 file system
# Automatically applies mod overrides when getting game objects
class Game:
    path: str
    modPaths: list[str]

    # takes the steam directory (where game files are stored) and documents directory (where mods are stored)
    def __init__(self, steamPath: str, documentsPath: str):
        self.path = steamPath

        # get descriptors
        dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
        with open(dlcLoadPath, 'r') as file:
            dlcLoad: dict = json.load(file)
        descriptorPaths = [os.path.join(documentsPath, descriptorPath) for descriptorPath in dlcLoad["enabled_mods"]]

        # get mod paths
        self.modPaths = []
        for descriptorPath in descriptorPaths:
            descriptor = parse.parse(descriptorPath, allowDuplicates=True)
            if "path" in descriptor:
                modPath = descriptor["path"]
            elif "archive" in descriptor:
                modPath = descriptor["archive"]
            else:
                raise KeyError(f"No path in descriptor: {descriptorPath}")
            self.modPaths.append(modPath)
    
    def getProvinceMap(self) -> provincemap.ProvinceMap:
        return provincemap.ProvinceMap(os.path.join(self.path, "map/provinces.bmp"))
