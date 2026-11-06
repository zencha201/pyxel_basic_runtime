"""Host for the BASIC core: PRINT output goes to the terminal buffer."""


class PyxelHost:
    def __init__(self, terminal):
        self.terminal = terminal

    def write(self, text):
        self.terminal.write(text)

    def column(self):
        return self.terminal.col
