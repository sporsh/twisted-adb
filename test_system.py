"""System test
"""
from twisted.internet import reactor
from twisted.internet.endpoints import clientFromString
from twisted.internet.protocol import ClientFactory
from client import AdbProtocolBase, connectMessage

if __name__ == '__main__':
    endpoint = clientFromString(reactor, "tcp:localhost:5555")

    factory = ClientFactory()
    factory.protocol = AdbProtocolBase

    def dispatchMessage(protocol, message):
        print "GOT MESSAGE:", message
        reactor.stop()
    factory.protocol.dispatchMessage = dispatchMessage

    client_d = endpoint.connect(factory)

    @client_d.addCallback
    def send_connect(client):
        print "TCP CONNECTED", client
        print "SENDING:", connectMessage
        client.sendMessage(connectMessage)

    reactor.run()
    print "DONE"
