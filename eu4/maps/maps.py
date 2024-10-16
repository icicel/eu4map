import eu4.files as files
import eu4.game as game


class DefaultMap(files.File):
    def __init__(self, game: game.Game):
        defaultMap = game.getFile("map/default.map")
        self.load(defaultMap)
