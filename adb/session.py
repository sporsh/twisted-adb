class AdbSession(object):
    def __init__(self, transport):
        self.streams = {}
        self.transport = transport

    def connectStream(self, destination, protocol):
        pass

    def closeStream(self, stream):
        pass
