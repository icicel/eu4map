import os

from eu4 import files

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"
DOCUMENTS_DIRECTORY = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis IV")
WORKSHOP_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/workshop/content/236850"


# Represents an EU4 file system, optionally with mods
# Automatically applies mod overrides when getting files
class Game:
    path: str
    mods: set["Mod"]
    loadOrder: list["Mod"]

    # Specify modloader=True to load ALL currently active mods from dlc_load.json
    # Specify mod to load a specific mod or list of mods,
    #   either directly by mod directory path (str) or by workshop ID (int)
    def __init__(self, modloader: bool = False, mod: str | int | list[str | int] | None = None):
        self.path = GAME_DIRECTORY

        # parse the mod argument
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
        
        # collect and sort defined mods
        self.mods = {Mod(modPath) for modPath in modPaths}
        if modloader:
            self.mods |= getActiveMods(DOCUMENTS_DIRECTORY)
        self.loadOrder = findLoadOrder(self.mods)


    # Take the last modded version found, otherwise vanilla
    def getFile(self, subpath: str) -> str:
        found = [mod for mod in self.loadOrder if os.path.exists(os.path.join(mod.path, subpath))]
        if not found:
            return os.path.join(self.path, subpath)
        if len(found) > 1:
            print(f"Warning: multiple mods provide {subpath}, using {found[-1]}")
        return os.path.join(found[-1].path, subpath)


# Represents an EU4 mod
# Mod names must be unique or the dependency system could break
class Mod:
    name: str
    path: str
    dependencies: list[str]
    def __init__(self, modPath: str):
        self.path = modPath
        if not os.path.exists(modPath):
            raise FileNotFoundError(f"Mod path not found: {modPath}")
        descriptorPath = os.path.join(modPath, "descriptor.mod")
        if not os.path.exists(descriptorPath):
            raise FileNotFoundError(f"No descriptor.mod in {modPath}")
        descriptor = files.File(descriptorPath)
        self.name = descriptor["name"]
        self.name.encode("cp1252")
        self.dependencies = descriptor.get("dependencies", default=[])
    
    def __repr__(self) -> str:
        return f"Mod({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)


# Returns a set of all active mods defined in dlc_load.json
def getActiveMods(documentsPath: str) -> set[Mod]:
    # get descriptors
    dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
    dlcLoad = files.File(dlcLoadPath, files.Filetype.JSON)
    descriptorPaths = [os.path.join(documentsPath, descriptorPath) for descriptorPath in dlcLoad["enabled_mods"]]

    # get mods
    mods = set()
    for descriptorPath in descriptorPaths:
        descriptor = files.File(descriptorPath)
        modPath = descriptor.get("path", default=None)
        if modPath is None:
            # the "archive" is usually already extracted by the launcher
            archivePath = descriptor.get("archive", default=None)
            if archivePath is None:
                raise KeyError(f"No path or archive in descriptor: {descriptorPath}")
            modPath = os.path.split(archivePath)[0]
        mods.add(Mod(modPath))
    
    return mods


# Returns a list of mods sorted by load order, taking dependencies into account
def findLoadOrder(mods: set[Mod]) -> list[Mod]:
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
