import json
import os
import eu4map.parse as parse

# Represents an EU4 file system
# Automatically applies mod overrides when getting files
class Files:
    vanillaPath: str
    mods: set["Mod"]
    loadOrder: list["Mod"]

    def __init__(self, steamPath: str, documentsPath: str | None = None):
        self.vanillaPath = steamPath
        if documentsPath is None:
            self.loadOrder = []
            return

        # get descriptors
        dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
        with open(dlcLoadPath, 'r') as file:
            dlcLoad: dict = json.load(file)
        descriptorPaths = [os.path.join(documentsPath, descriptorPath) for descriptorPath in dlcLoad["enabled_mods"]]

        # get mods
        self.mods = set()
        modsByName: dict[str, Mod] = {}
        for descriptorPath in descriptorPaths:
            mod = Mod(descriptorPath)
            self.mods.add(mod)
            modsByName[mod.name] = mod
        
        # find dependents (other mods that have it as dependency) per mod
        dependents: dict[Mod, list[Mod]] = {}
        for mod in self.mods:
            for dependencyName in mod.dependencies:
                if dependencyName not in modsByName:
                    # missing dependencies are allowed
                    continue
                dependency = modsByName[dependencyName]
                dependents.setdefault(dependency, []).append(mod)
        
        # calculate load order
        # mods are sorted alphabetically, then dependents are added before the mod itself
        self.loadOrder = []
        modSortOrder = sorted(list(self.mods), key=lambda mod: mod.name)
        for mod in modSortOrder:
            if mod in self.loadOrder:
                continue
            self.loadOrder.extend([dependent for dependent in dependents.get(mod, []) if dependent not in self.loadOrder])
            self.loadOrder.append(mod)

    # Take the last modded version found, otherwise vanilla
    def getFile(self, subpath: str) -> str:
        for mod in self.loadOrder:
            fullPath = os.path.join(mod.path, subpath)
            if os.path.exists(fullPath):
                filePath = fullPath
        if filePath is None:
            return os.path.join(self.vanillaPath, subpath)
        return filePath

class Mod:
    name: str
    path: str
    dependencies: list[str]
    def __init__(self, descriptorPath: str):
        descriptor = parse.parse(descriptorPath, allowDuplicates=True)
        self.name = descriptor["name"]
        self.name.encode("cp1252")
        if "path" in descriptor:
            self.path = descriptor["path"]
        elif "archive" in descriptor:
            # the "archive" is usually already extracted
            self.path = os.path.split(descriptor["archive"])[0]
        else:
            raise KeyError(f"No path in descriptor: {descriptorPath}")
        self.dependencies = descriptor.get("dependencies", [])
    
    def __repr__(self) -> str:
        return f"Mod({self.name})"
