import enum
from typing import Any

from eu4 import parse

# Contains generic classes which can be extended to represent specific types of files
# They can also be used as-is to represent files "anonymously"


# Filetype enum
class Filetype(enum.Enum):
    CW = 0
    JSON = 1
    LUA = 2
    CSV = 3
    YML = 4


# Generic scope file object
class File:
    scope: parse.Scope
    def __init__(self, path: str, filetype: Filetype = Filetype.CW):
        if filetype == Filetype.CW:
            self.scope = parse.parse(path)
        elif filetype == Filetype.JSON:
            self.scope = parse.parseJson(path)
        elif filetype == Filetype.LUA:
            raise NotImplementedError("Lua parsing not implemented")
        elif filetype == Filetype.CSV:
            raise NotImplementedError("CSV parsing not implemented")
        elif filetype == Filetype.YML:
            raise NotImplementedError("Localization parsing not implemented")
        else:
            raise ValueError(f"Invalid filetype: {filetype}")
    
    def __iter__(self):
        return iter(self.scope.scope)
    
    def __getitem__(self, key: str) -> Any:
        result = self.getAll(key)
        if len(result) == 1:
            return result[0]
        if len(result) > 1:
            raise ValueError(f"Duplicate key, use iteration: {key}")
        raise KeyError(f"Key not found: {key}")
    
    def __contains__(self, key: str) -> bool:
        return any(k == key for k, _ in self)
    
    def get(self, key: str, default: Any) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
    
    def getAll(self, key: str) -> list[Any]:
        return [v for k, v in self if k == key]
