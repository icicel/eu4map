import ClauseWizard as cw

# Parse a Clausewitz Engine script file
def parse(path: str) -> dict:
    with open(path, 'r', encoding="cp1252") as file:
        text = file.read()
    raw = cw.cwparse(text)
    return parseScope(raw)

# ClauseWizard.cwparse returns a large nested list with an obtuse but regular structure
# Further processing is needed to turn it into a more useful dictionary
def parseScope(tokens: list[tuple[str, list]]) -> dict:
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
            scope[key] = parseScope(item)
        # array
        elif len(item[0]) == 1:
            scope[key] = [subitem[0] for subitem in item]
        # invalid
        else:
            raise ValueError(f"Invalid item: {item}")
    if len(tokens) != len(scope):
        raise ValueError(f"Duplicate keys: {tokens}")
    return scope
