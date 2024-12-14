import os

from eu4 import files

GAME_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV"
DOCUMENTS_DIRECTORY = os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis IV")
WORKSHOP_DIRECTORY = "C:/Program Files (x86)/Steam/steamapps/workshop/content/236850"


class Game:
    '''
    An EU4 file system, optionally with mods. Works from three directories:
    - The game directory, containing the game's files. This is the Steam installation directory and is
    located at `C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV`.
    - The documents directory, containing user data and mods. This is located at
    `C:/Users/(username)/Documents/Paradox Interactive/Europa Universalis IV`.
    - The Workshop directory, containing all Steam Workshop mods. This is located at
    `C:/Program Files (x86)/Steam/steamapps/workshop/content/236850`.
    '''

    path: str
    '''The game directory path'''
    mods: set["Mod"]
    '''A set of all loaded mods'''
    loadOrder: list["Mod"]
    '''A list of all loaded mods, sorted by load order (with the last mod having the highest priority). Takes
    dependencies into account'''

    def __init__(self, modloader: bool = False, mod: str | int | list[str | int] | None = None):
        '''
        :param modloader: Whether to load all mods currently enabled in the launcher (from `dlc_load.json`)
        :param mod: An optional mod or list of mods to load. A "mod" in this case can be a directory
        path (str) or a Steam Workshop ID (int). Will be loaded in addition to enabled mods if `modloader` is true
        '''

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
            if override is None: # mod doesn't override the file
                continue
            currentFile = override
            replacingMod = mod
        if currentFile == "":
            raise FileNotFoundError(f"File not found: {subpath}, removed by {replacingMod}")
        return currentFile


class Descriptor(files.ScopeFile):
    '''
    Represents a descriptor file, which defines a mod's metadata, dependencies and the location of the mod directory.
    '''

    name: str
    '''The mod's name'''
    path: str | None
    '''The path to the mod's directory. Mutually exclusive with `Descriptor.archive`'''
    archive: str | None
    '''The path to the mod's archive file. Mutually exclusive with `Descriptor.path`'''
    workshopID: str | None
    '''The Steam Workshop ID of the mod, if it is a Workshop mod. Optional'''
    supportedVersion: str
    '''The version of the game the mod is compatible with. Doesn't really matter as mod compatibility is not enforced'''
    replacePath: list[str]
    '''A list of subpaths in the game directory to completely replace with the mod's files'''

    def __init__(self, path: str):
        '''
        :param path: The path to the file
        '''
        super().__init__(path)
        self.name: str = self.scope["name"]
        self.path: str | None = self.scope.get("path", default=None)
        self.archive: str | None = self.scope.get("archive", default=None)
        self.workshopID: str | None = self.scope.get("remote_file_id", default=None)
        self.supportedVersion: str = self.scope.get("supported_version", default="?")
        self.replacePath: list[str] = self.scope.getAll("replace_path")
        self.dependencies: list[str] = self.scope.get("dependencies", default=[])


# Represents an EU4 mod
# Mod names must be unique or the dependency system could break
class Mod:
    '''
    An EU4 mod, or technically, a directory containing a mod.
    '''
    
    name: bytes
    '''The mod's name, encoded in `cp1252`. The encoding is necessary so that mods with names that start
    with lowercase letters are loaded after those that start with uppercase letters (as the game does)'''
    technicalName: str | int
    '''The mod's technical name. This is either the directory name (str) or the Steam Workshop ID (int)'''
    path: str
    '''The path to the mod directory'''
    dependencies: list[str]
    '''A list of mod names that this mod depends on. These should be loaded before this mod'''
    replacePaths: list[str]
    '''A list of game directories to completely replace with this mod's files, instead of merging as
    the game normally does'''

    def __init__(self, modPath: str):
        '''
        :param modPath: The path to the mod directory
        '''
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


def getAllMods(documentsPath: str) -> set[Mod]:
    '''
    Returns a set of all mods currently installed.

    :param documentsPath: The path to the documents directory
    '''
    modsPath = os.path.join(documentsPath, "mod")
    # Find all descriptor files in the mod directory
    descriptorPaths = [os.path.join(modsPath, filename)
                       for filename in os.listdir(modsPath)
                       if filename.endswith(".mod")]
    return getModsFromDescriptors(descriptorPaths)


def getActiveMods(documentsPath: str) -> set[Mod]:
    '''
    Returns a set of all mods currently enabled in the launcher.

    :param documentsPath: The path to the documents directory
    '''
    dlcLoadPath = os.path.join(documentsPath, "dlc_load.json")
    dlcLoad = files.JsonFile(dlcLoadPath)
    # Find all descriptor files defined in dlc_load.json
    descriptorPaths = [os.path.join(documentsPath, descriptorSubpath)
                       for descriptorSubpath in dlcLoad["enabled_mods"]]
    return getModsFromDescriptors(descriptorPaths)


def getModsFromDescriptors(descriptorPaths: list[str]) -> set[Mod]:
    '''
    Initializes a set of mods from a list of descriptor files.

    :param descriptorPaths: A list of paths to descriptor files
    '''
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


def findLoadOrder(mods: set[Mod]) -> list[Mod]:
    '''
    Sorts a set of mods by load order. Usually, mods are loaded in alphabetical order, but if a mod has
    dependencies defined in its descriptor, those mods will be loaded first.

    Note that since mod names are encoded in `cp1252`, mod names that start with lowercase letters will be
    loaded after those that start with uppercase letters, matching the game's behavior.

    :param mods: A set of mods
    '''
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
    # mods are sorted alphabetically, then dependencies are moved before the mod(s) that depends on them
    loadOrder = []
    modSortOrder = sorted(list(mods), key=lambda mod: mod.name)
    for mod in modSortOrder:
        if mod in loadOrder: # already added (due to dependency)
            continue
        loadOrder.extend([dependent for dependent in dependents.get(mod, []) if dependent not in loadOrder])
        loadOrder.append(mod)
    
    return loadOrder
