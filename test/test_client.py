from twisted.trial.unittest import TestCase
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor, defer
from adb.client import AdbClient
from adb.stream import AdbStream
from twisted.internet.error import ConnectionDone

class MockProto(object):
    def dataReceived(self, data):
        print "RECEIVED DATA: %r" % data

class AdbClientTest(TestCase):
    def setUp(self):
        self.endpoint = clientFromString(reactor, "tcp:gsporshe-zydeco:5555:timeout=5")

    def test_connect(self):
        connectionLostDeferred = defer.Deferred()
        self.assertFailure(connectionLostDeferred, ConnectionDone)

        sessionConnectedDeferred = defer.Deferred()
        @sessionConnectedDeferred.addCallback
        def checkSystemIdentityString(systemIdentityString):
            self.assertSubstring('device', systemIdentityString)

        factory = AdbClient()
        d = self.endpoint.connect(factory)

        @d.addCallback
        def connectionMade(client):
            @sessionConnectedDeferred.addCallback
            def disconnectSession(systemIdentityString):
                client.transport.loseConnection()
            client.sessionConnected = sessionConnectedDeferred.callback
            client.connectionLost = connectionLostDeferred.callback
            return defer.DeferredList((sessionConnectedDeferred,
                                       connectionLostDeferred),
                                      fireOnOneErrback=True, consumeErrors=True)
        return d

    def test_stream(self):
        connectionLostDeferred = defer.Deferred()
        self.assertFailure(connectionLostDeferred, ConnectionDone)

        stream = AdbStream(destination, protocol)

        factory = AdbClient()
        d = self.endpoint.connect(factory)

        @d.addCallback
        def connectionMade(client):
            @sessionConnectedDeferred.addCallback
            def openStream(systemIdentityString):
                client.openStream(stream)
            client.sessionConnected = sessionConnectedDeferred.callback
            client.connectionLost = connectionLostDeferred.callback
            return defer.DeferredList((sessionConnectedDeferred,
                                       connectionLostDeferred),
                                      fireOnOneErrback=True, consumeErrors=True)
        return d
