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
            modlist = mod
            for mod in modlist:
                if isinstance(mod, int):
                    modPaths.append(os.path.join(WORKSHOP_DIRECTORY, str(mod)))
                elif mod:
                    modPaths.append(mod)
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
    name: bytes # encoded in cp1252
    technicalName: str | int # either the directory name or the workshop ID
    path: str
    dependencies: list[str]
    def __init__(self, modPath: str):
        self.path = modPath
        if not os.path.exists(modPath):
            raise FileNotFoundError(f"Mod path not found: {modPath}")

        descriptorPath = os.path.join(modPath, "descriptor.mod")
        if not os.path.exists(descriptorPath):
            # Found no descriptor.mod, search for any .mod file
            for filename in os.listdir(modPath):
                if filename.endswith(".mod"):
                    descriptorPath = os.path.join(modPath, filename)
                    break
            else:
                raise FileNotFoundError(f"No descriptor in {modPath}")
        descriptor = files.ScopeFile(descriptorPath)

        rawName: str = descriptor["name"]
        self.name = rawName.encode("cp1252")

        directoryName = os.path.split(modPath)[1]
        try:
            self.technicalName = int(directoryName)
        except ValueError:
            self.technicalName = directoryName

        self.dependencies = descriptor.get("dependencies", default=[])
    
    def __repr__(self) -> str:
        return f"Mod({self.technicalName}, {self.name})"

    def __hash__(self) -> int:
        return hash(self.name)


# Returns a set of all mods with .mod files in the mods directory
def getAllMods(documentsPath: str) -> set[Mod]:
    modsPath = os.path.join(documentsPath, "mod")
    descriptorPaths = [os.path.join(modsPath, filename)
                       for filename in os.listdir(modsPath)
                       if filename.endswith(".mod")]
    return _getModsFromDescriptors(descriptorPaths)


# Returns a set of all active mods defined in dlc_load.json
def getActiveMods(documentsPath: str) -> set[Mod]:
    dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
    dlcLoad = files.JsonFile(dlcLoadPath)
    descriptorPaths = [os.path.join(documentsPath, descriptorSubpath)
                       for descriptorSubpath in dlcLoad["enabled_mods"]]
    return _getModsFromDescriptors(descriptorPaths)


def _getModsFromDescriptors(descriptorPaths: list[str]) -> set[Mod]:
    mods = set()
    for descriptorPath in descriptorPaths:
        descriptor = files.ScopeFile(descriptorPath)
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
