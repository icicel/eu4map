import json
import os
import eu4map.parse as parse

# Represents an EU4 file system
# Automatically applies mod overrides when getting files
class Gamefiles:
    vanillaPath: str
    modPaths: list[str]

    def __init__(self, steamPath: str, documentsPath: str):
        self.vanillaPath = steamPath

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
    
    def provinces_bmp(self) -> str:
        for modPath in self.modPaths:
            path = os.path.join(modPath, "map/provinces.bmp")
            if os.path.exists(path):
                return path
        return os.path.join(self.vanillaPath, "map/provinces.bmp")
