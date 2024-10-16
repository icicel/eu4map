import json
import ClauseWizard as cw

from typing import Any
type Item = Value | list[Value] | Scope
type Value = str | int | float | bool


# A scope is a list of items, each with a string key that may or may not be unique
class Scope:
    scope: list[tuple[str, Item]]
    def __init__(self, tokens: list[tuple[str, list]]):
        self.scope = []
        # Item tokens can either be:
        # - a constant (singleton list of a value)
        # - an array (list of singleton lists of values)
        # - a scope (list of string-list pairs)
        # Values can be strings, ints, floats or booleans
        for key, item in tokens:
            # constant
            if not isinstance(item[0], list):
                self.append(key, item[0])
            # array
            elif len(item[0]) == 1:
                self.append(key, [subitem[0] for subitem in item])
            # scope
            elif len(item[0]) == 2:
                self.append(key, Scope(item))
            # invalid
            else:
                raise ValueError(f"Invalid item: {item}")
    
    def __getitem__(self, key: str) -> Any:
        result = [v for k, v in self if k == key]
        if len(result) == 1:
            return result[0]
        if len(result) > 1:
            raise ValueError(f"Duplicate key, use iteration: {key}")
        raise KeyError(f"Key not found: {key}")
    
    def __iter__(self):
        return iter(self.scope)
    
    def __contains__(self, key: str) -> bool:
        return any(k == key for k, _ in self)

    def append(self, key: str, item: Item):
        self.scope.append((key, item))
    
    def get(self, key: str, default: Any) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
    
    def getAll(self, key: str) -> list[Any]:
        return [v for k, v in self if k == key]


# Parse a Clausewitz Engine script file
# The top-level object of a file is always a scope
def parse(path: str) -> Scope:
    with open(path, 'r', encoding="cp1252") as file:
        text = file.read()
    raw = cw.cwparse(text)
    return Scope(raw)


# How EU4 handles JSON
def parseJson(path: str) -> dict[str, str]:
    with open(path, 'r') as file:
        return json.load(file)
