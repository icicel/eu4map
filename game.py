
# Represents an EU4 file system
# Automatically applies mod overrides when getting game objects
class Game:
    path: str
    modPaths: list[str]

    # takes the game directory and optionally a list of mod directories
    def __init__(self, path: str, modPaths: list[str] = []):
        if modPaths:
            raise NotImplementedError("Use vanilla plz :>")
        self.path = path
        self.modPaths = modPaths
