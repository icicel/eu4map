
'''
Contains various generic classes that can be extended to represent specific types of files. They can also
be used as-is to represent files "anonymously".

An important data structure utilized by this module is Scope, which is used to represent the kinds of
key-value objects utilized by Clausewitz scripting files. Unlike how such structures are usually
implemented, a Scope may have multiple items with the same key, and the order of items is preserved.
'''

import ClauseWizard as cw
import csv
import enum
import json

from typing import Any

type Item = Value | list[Value] | Scope
type Value = str | int | float | bool


# An ordered list of key-item pairs where keys do not have to be unique
class Scope:
    '''
    An ordered list of key-item pairs where keys do not have to be unique and items are optional. Items can
    be constants (str, int, float or bool), arrays (list of constants) or nested scopes. Keys must be strings.

    By convention, an empty string represents the lack of an item for a key.
    '''

    scope: list[tuple[str, Item]]
    '''The list of key-item pairs in this scope'''

    def __init__(self):
        self.scope = []
    
    def __iter__(self):
        return iter(self.scope)
    
    def getAll(self, key: str) -> list[Any]:
        '''
        Returns a list of all items with the given key, in order of appearance. If the key is not found, an
        empty list is returned.

        :param key: The key to search for
        :return: A list of all items with the given key
        '''
        return [v for k, v in self if k == key]
    
    def _get(self, key: str) -> Any | None:
        '''
        Returns the last item with the given key, no matter its type. If the key is not found, None is returned.

        :param key: The key to search for
        :return: The last item with the given key
        '''
        result = self.getAll(key)
        return result[-1] if result else None
    
    def getConst(self, key: str, default: Any = "") -> Any:
        '''
        Returns the last constant (str, int, float or bool) with the given key. If the key is not found,
        the default value is returned. If the key has no item, an empty string is returned.

        :param key: The key to search for
        :param default: The value to return if the search fails
        :return: The last item with the given key
        '''
        result = self._get(key)
        if result == "":
            return ""
        if result is None or type(result) is list or type(result) is Scope:
            return default
        return result
    
    def getArray(self, key: str, default: Any = "") -> list[Any]:
        '''
        Returns the last array with the given key. If the key is not found, the default value is
        returned. If the key has no item, an empty list is returned.

        :param key: The key to search for
        :param default: The value to return if the search fails
        :return: The last item with the given key
        '''
        result = self._get(key)
        if result == "":
            return []
        if result is None or type(result) is not list:
            return default
        return result
    
    def getScope(self, key: str, default: Any = "") -> "Scope":
        '''
        Returns the last scope with the given key. If the key is not found, the
        default value is returned. If the key has no item, an empty scope is returned.

        :param key: The key to search for
        :param default: The value to return if the search fails
        :return: The last item with the given key
        '''
        result = self._get(key)
        if result == "":
            return Scope()
        if result is None or type(result) is not Scope:
            return default
        return result

    def append(self, key: str, item: Item):
        '''
        Append a key-item pair to the end of the scope.

        :param key: The key of the pair
        :param item: The item of the pair, or an empty string if it's missing
        '''
        self.scope.append((key, item))

class ScopeFile:
    '''
    A generic object representing a Clausewitz script file. The file is parsed into a Scope object and can be
    accessed through the `scope` attribute.
    '''

    scope: Scope
    '''The scope object representing the contents of the file'''
    path: str
    '''The path to the file represented by this object'''

    def __init__(self, path: str):
        '''
        :param path: The path to the file
        '''
        self.path = path
        with open(self.path, 'r', encoding="cp1252") as file:
            text = file.read()
        try:
            tokens = cw.cwparse(text)
        # If the parsing fails, ClauseWizard raises a pyparsing.exceptions.ParseException.
        # We catch it and raise a ValueError with a more informative message.
        except Exception as parseException:
            raise ValueError(f"Failed to parse scope file '{self.path}'") from parseException
        self.scope = _parseTokens(tokens)

def _parseTokens(tokens: list[tuple[str, list]]) -> Scope:
    '''
    Parse the tokens generated by `ClauseWizard.cwparse` into a Scope object.

    The structure of the tokens is a list of key-item pairs, where the key is a string and the item is:
    - if a constant, a singleton list of the value
    - if an array, a list of singleton lists of values
    - if a scope, a list of string-list pairs (which is recursively parsed)
    - if empty, a list with a single empty string

    :param tokens: The tokens to parse
    :return: The parsed scope
    '''
    scope = Scope()
    for key, item in tokens:
        # empty
        if not item[0]:
            scope.append(key, "")
        # constant
        elif not isinstance(item[0], list):
            scope.append(key, item[0])
        # array
        elif len(item[0]) == 1:
            scope.append(key, [subitem[0] for subitem in item])
        # scope
        elif len(item[0]) == 2:
            scope.append(key, _parseTokens(item))
        # invalid
        else:
            raise ValueError(f"Invalid item: {item}")
    return scope


class JsonFile:
    '''
    A JSON file represented as a dictionary.
    '''

    json: dict
    '''The dictionary representing the contents of the file'''
    path: str
    '''The path to the file represented by this object'''

    def __init__(self, path: str):
        '''
        :param path: The path to the file
        '''
        self.path = path
        with open(self.path, 'r') as file:
            self.json = json.load(file)
        
    def __getitem__(self, key: str) -> Any:
        return self.json[key]


class CsvFile:
    '''
    A CSV file represented as a list of rows, where each row is a list of strings.
    '''

    csv: list[list[str]]
    '''The list representing the contents of the file'''
    path: str
    '''The path to the file represented by this object'''

    def __init__(self, path: str):
        '''
        :param path: The path to the file
        '''
        self.path = path
        with open(self.path, 'r', encoding="cp1252", errors="ignore") as file:
            self.csv = [row for row in csv.reader(file, delimiter=';', quotechar=None)]
        self.csv.pop(0)
    
    def __iter__(self):
        return iter(self.csv)


class NoneEnum(enum.Enum):
    '''
    A generic enum that represents all values not part of the enum as None. This means when converting
    from a value to the enum, if the value isn't part of the enum, it will be converted to the None
    value.

    Naturally, all enums that extend this class must have None as a valid value.
    '''

    @classmethod
    def _missing_(cls, _) -> Any:
        return cls(None)
