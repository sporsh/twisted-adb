"""System test
"""
from twisted.internet import reactor
from twisted.internet.endpoints import clientFromString
from twisted.internet.protocol import ClientFactory
from adb import protocol

def main():
    endpoint = clientFromString(reactor, "tcp:localhost:5555:timeout=5")
#    endpoint = clientFromString(reactor, "unix:/dev/bus/usb/001/012")

    factory = ClientFactory()
    factory.protocol = protocol.AdbProtocolBase

    data = []

    def adb_CNXN(client, message):
        print "GOT MESSAGE", message
        client.sendCommand(protocol.CMD_OPEN, 2, message.arg0, 'shell:ls\x00')
    def adb_WRTE(client, message):
        print "GOT MESSAGE", message
        data.append(message.data)
        client.sendCommand(protocol.CMD_OKAY, 2, message.arg0, '')
    def adb_CLSE(client, message):
        print "GOT MESSAGE", message
        client.sendCommand(protocol.CMD_CLSE, 2, message.arg0, '')
        reactor.stop()
    factory.protocol.adb_CNXN = adb_CNXN
    factory.protocol.adb_WRTE = adb_WRTE
    factory.protocol.adb_CLSE = adb_CLSE

    client_d = endpoint.connect(factory)

    @client_d.addCallback
    def send_connect(client):
        print "TCP CONNECTED", client
        client.sendCommand(protocol.CMD_CNXN,
                           protocol.VERSION,
                           protocol.MAX_PAYLOAD,
                           'host::\x00')

    @client_d.addErrback
    def connection_failed(reason):
        print reason.getErrorMessage()
        reactor.stop()

    reactor.run()
    print "DONE", ''.join(data).splitlines()

if __name__ == '__main__':
    main()
