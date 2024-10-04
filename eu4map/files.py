import json
import os
import eu4map.parse as parse

# Represents an EU4 file system
# Automatically applies mod overrides when getting files
class Files:
    vanillaPath: str
    mods: set["Mod"]
    loadOrder: list["Mod"]

    # steamPath: path to the game's steam directory
    # documentsPath: path to the game's documents directory
    #   (for loading active mods from dlc_load.json, skipped if None)
    # modPaths: optional list of additional mod paths
    def __init__(self, steamPath: str, documentsPath: str | None, modPaths: list[str]):
        self.vanillaPath = steamPath

        self.mods = set()
        # add active mods
        if documentsPath:
            self.mods |= getActiveMods(documentsPath)
        # add additional mods
        if modPaths:
            self.mods |= {Mod(modPath) for modPath in modPaths}

        self.loadOrder = findLoadOrder(self.mods)

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
    def __init__(self, modPath: str):
        self.path = modPath
        descriptorPath = os.path.join(modPath, "descriptor.mod")
        if not os.path.exists(descriptorPath):
            raise FileNotFoundError(f"No descriptor.mod in {modPath}")
        descriptor = parse.parse(descriptorPath, allowDuplicates=True)
        self.name = descriptor["name"]
        self.name.encode("cp1252")
        self.dependencies = descriptor.get("dependencies", [])
    
    def __repr__(self) -> str:
        return f"Mod({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

def getActiveMods(documentsPath: str) -> set["Mod"]:
    # get descriptors
    dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
    with open(dlcLoadPath, 'r') as file:
        dlcLoad: dict = json.load(file)
    descriptorPaths = [os.path.join(documentsPath, descriptorPath) for descriptorPath in dlcLoad["enabled_mods"]]

    # get mods
    mods = set()
    for descriptorPath in descriptorPaths:
        descriptor = parse.parse(descriptorPath, allowDuplicates=True)
        if "path" in descriptor:
            modPath = descriptor["path"]
        elif "archive" in descriptor: # the "archive" is usually already extracted
            modPath = os.path.split(descriptor["archive"])[0]
        else:
            raise KeyError(f"No path in descriptor: {descriptorPath}")
        mods.add(Mod(modPath))
    
    return mods
    
def findLoadOrder(mods: set["Mod"]) -> list["Mod"]:
    modIndex = {mod.name: mod for mod in mods}

    # find dependents per mod (all other mods that have it as dependency)
    dependents: dict[Mod, list[Mod]] = {}
    for mod in mods:
        for dependencyName in mod.dependencies:
            if dependencyName not in modIndex:
                # missing dependencies are allowed
                continue
            dependency = modIndex[dependencyName]
            dependents.setdefault(dependency, []).append(mod)

    # calculate load order
    # mods are sorted alphabetically, then dependents are added before the mod itself
    loadOrder = []
    modSortOrder = sorted(list(mods), key=lambda mod: mod.name)
    for mod in modSortOrder:
        if mod in loadOrder:
            continue
        loadOrder.extend([dependent for dependent in dependents.get(mod, []) if dependent not in loadOrder])
        loadOrder.append(mod)
    
    return loadOrder
