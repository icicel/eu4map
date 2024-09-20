import ClauseWizard as cw

# Parse a Clausewitz Engine script file
# Set allowDuplicates to True to not raise an error on duplicate keys
# (subsequent keys will in that case overwrite previous ones)
def parse(path: str, allowDuplicates: bool = False) -> dict:
    with open(path, 'r', encoding="cp1252") as file:
        text = file.read()
    raw = cw.cwparse(text)
    return parseScope(raw, allowDuplicates)

# ClauseWizard.cwparse returns a large nested list with an obtuse but regular structure
# Further processing is needed to turn it into a more useful dictionary
def parseScope(tokens: list[tuple[str, list]], allowDuplicates: bool) -> dict:
    scope = {}
    # Items can either be:
    # - a constant (singleton list of a value)
    # - a scope (list of string-list pairs)
    # - an array (list of singleton lists of values)
    # Values can be strings, ints, floats or booleans
    # The top-level object is always a scope
    for key, item in tokens:
        # constant
        if not isinstance(item[0], list):
            scope[key] = item[0]
        # scope
        elif len(item[0]) == 2:
            scope[key] = parseScope(item, allowDuplicates)
        # array
        elif len(item[0]) == 1:
            scope[key] = [subitem[0] for subitem in item]
        # invalid
        else:
            raise ValueError(f"Invalid item: {item}")
    if len(tokens) != len(scope) and not allowDuplicates:
        raise ValueError(f"Duplicate keys: {tokens}")
    return scope
