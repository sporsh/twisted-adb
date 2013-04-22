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
        print "CONNECT SESSION"
        self.factory.sessions[systemIdentityString] = self
        self.factory.sessionConnected(self)


class AdbClient(ClientFactory):
    sessions = None
    protocol = AdbClientProtocol
    def __init__(self, systemType='host', serialNumber='', banner=''):
        self.sessionDeferred = defer.Deferred()
        self.sessions = {}
        self.systemType=systemType
        self.serialNumber = serialNumber
        self.banner = banner

    def sessionConnected(self, session):
        self.sessionDeferred.callback(session)
