from zope.interface.declarations import implements
from twisted.internet import interfaces


class AdbStream(object):
    implements(interfaces.ITransport,
               interfaces.IProtocol)

    def __init__(self, destination, protocol):
        self.conn = None
        self.localId = None
        self.remoteId = None
        self.destination = destination
        self.protocol = protocol

    def write(self, data):
        """Write data over the stream in a non-blocking fashion.
        """

    def writeSequence(self, data):
        """Write a list of strings to the stream.
        """

    def loseConnection(self):
        """Close stream after writing all pending data
        """

    def getPeer(self):
        """Get the remote address of this connection
        """

    def getHost(self):
        """Similar to getPeer, but returns an address describing this side of
        the connection.
        """

    def ready(self, remoteId):
        pass

    def close(self, reason):
        pass
