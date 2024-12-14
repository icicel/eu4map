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

    def getFile(self, subpath: str) -> str:
        '''
        Takes a game directory subpath to a file and returns the absolute path to the file. Simulates mod
        overrides, returning the path to the overriding modded file if needed.

        If multiple mods change the file, then the last mod in the load order will have priority. This
        means that if a mod defines `replace_path` on the parent directory and removes the file, and no
        higher-priority mod has a replacement file, it will not be found and this method will throw an error.

        :param subpath: A file path relative to the game directory (ex: `map/definition.csv`)
        '''
        currentFile = os.path.join(self.path, subpath)
        replacingMod = None
        # Apply mods according to load order
        for mod in self.loadOrder:
            override = mod.overrideFile(subpath)
            if override is None:
                continue
            currentFile = override
            replacingMod = mod
        if currentFile == "":
            raise FileNotFoundError(f"File not found: {subpath}, removed by {replacingMod}")
        return currentFile


class Descriptor(files.ScopeFile):
    def __init__(self, path: str):
        super().__init__(path)
        self.name: str = self.scope["name"]
        self.path: str | None = self.scope.get("path", default=None)
        self.archive: str | None = self.scope.get("archive", default=None)
        self.remoteFileId: str | None = self.scope.get("remote_file_id", default=None)
        self.supportedVersion: str = self.scope.get("supported_version", default="?")
        self.replacePath: list[str] = self.scope.getAll("replace_path")
        self.dependencies: list[str] = self.scope.get("dependencies", default=[])


# Represents an EU4 mod
# Mod names must be unique or the dependency system could break
class Mod:
    name: bytes # encoded in cp1252
    technicalName: str | int # either the directory name or the workshop ID
    path: str
    dependencies: list[str]
    replacePaths: list[str]
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
        descriptor = Descriptor(descriptorPath)

        rawName: str = descriptor.name
        self.name = rawName.encode("cp1252")

        directoryName = os.path.split(modPath)[1]
        try:
            self.technicalName = int(directoryName)
        except ValueError:
            self.technicalName = directoryName

        self.dependencies = descriptor.dependencies

        self.replacePaths = descriptor.replacePath
    
    def __repr__(self) -> str:
        return f"Mod({self.technicalName}, {self.name})"

    def __hash__(self) -> int:
        return hash(self.name)
    
    def overrideFile(self, subpath: str) -> str | None:
        '''
        Takes a subpath to a game file and returns:
        - The absolute path to the file if the mod provides it
        - An empty string if the mod removes the file (by replacing the parent directory using `replace_path`)
        - `None` if the mod doesn't provide or remove the file

        :param subpath: A file path relative to the game directory
        '''
        moddedFile = os.path.join(self.path, subpath)
        if os.path.exists(moddedFile):
            return moddedFile
        # The mod doesn't provide the file
        # If it then replaces the parent directory of the file, it's effectively removed
        for replacePath in self.replacePaths:
            if subpath.startswith(replacePath):
                return ""
        # The mod doesn't provide the file and doesn't replace it
        return None


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
        descriptor = Descriptor(descriptorPath)
        modPath = descriptor.path
        if modPath is None:
            # the "archive" is usually already extracted by the launcher
            archivePath = descriptor.archive
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
