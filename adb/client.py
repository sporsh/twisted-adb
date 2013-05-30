from twisted.internet.protocol import ClientFactory
from adb.protocol import AdbProtocolBase
from twisted.internet import defer

class AdbClientProtocol(AdbProtocolBase):
    def __init__(self):
        AdbProtocolBase.__init__(self)
        self.sessionDeferred = defer.Deferred()

    def connectionMade(self):
        self.connectSession(self.factory.systemType,
                            self.factory.serialNumber,
                            self.factory.banner)

    def sessionConnected(self, systemIdentityString):
        print "SESSION CONNECTED"


class AdbClient(ClientFactory):
    protocol = AdbClientProtocol

    def __init__(self, systemType='host', serialNumber='', banner=''):
        self.systemType=systemType
        self.serialNumber = serialNumber
        self.banner = banner
