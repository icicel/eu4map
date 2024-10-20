import ClauseWizard as cw
import json

type Item = Value | list[Value] | Scope
type Value = str | int | float | bool


# An ordered list of key-item pairs where keys do not have to be unique
# Should be read using a wrapper class like eu4.files.File
class Scope:
    scope: list[tuple[str, Item]]
    def __init__(self):
        self.scope = []

    def append(self, key: str, item: Item):
        self.scope.append((key, item))


# Parse a Clausewitz Engine script file
# The top-level object of a file is always a scope
def parse(path: str) -> Scope:
    with open(path, 'r', encoding="cp1252") as file:
        text = file.read()
    tokens = cw.cwparse(text)
    return parseTokens(tokens)
def parseTokens(tokens: list[tuple[str, list]]) -> Scope:
    scope = Scope()
    # Item tokens can either be:
    # - a constant (singleton list of a value)
    # - an array (list of singleton lists of values)
    # - a scope (list of string-list pairs)
    # Values can be strings, ints, floats or booleans
    for key, item in tokens:
        # constant
        if not isinstance(item[0], list):
            scope.append(key, item[0])
        # array
        elif len(item[0]) == 1:
            scope.append(key, [subitem[0] for subitem in item])
        # scope
        elif len(item[0]) == 2:
            scope.append(key, parseTokens(item))
        # invalid
        else:
            raise ValueError(f"Invalid item: {item}")
    return scope


# Simple conversion of a JSON file to a Scope
def parseJson(path: str) -> Scope:
    scope = Scope()
    with open(path, 'r') as file:
        jsonObject: dict = json.load(file)
        for key, value in jsonObject.items():
            scope.append(key, value)
    return scope
