import json
import os
import eu4map.parse as parse

# Represents an EU4 file system
# Automatically applies mod overrides when getting files
class Files:
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
                # the "archive" is usually already extracted
                modPath = os.path.split(descriptor["path"])[0]
            else:
                raise KeyError(f"No path in descriptor: {descriptorPath}")
            self.modPaths.append(modPath)
    
    # Take the first modded version found, otherwise vanilla
    def simpleFile(self, subpath: str) -> str:
        for modPath in self.modPaths:
            path = os.path.join(modPath, subpath)
            if os.path.exists(path):
                return path
        return os.path.join(self.vanillaPath, subpath)