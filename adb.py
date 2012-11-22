"""
@author: Geir Sporsheim
@see: git repo https://android.googlesource.com/platform/system/core/
@see: source file adb/adb.h
"""

from twisted.internet import protocol, reactor, defer
from twisted.internet.endpoints import clientFromString
from twisted.internet.protocol import ClientFactory
import struct

MAX_PAYLOAD = 4096

A_SYNC = 0x434e5953
A_CNXN = 0x4e584e43
A_OPEN = 0x4e45504f
A_OKAY = 0x59414b4f
A_CLSE = 0x45534c43
A_WRTE = 0x45545257

A_VERSION = 0x01000000 # ADB protocol version
ADB_VERSION_MAJOR = 1 # Used for help/version information
ADB_VERSION_MINOR = 0 # Used for help/version information
ADB_SERVER_VERSION = 20 # Increment this when we want to force users to start a new adb server

class AdbMessage(object):
    def __init__(self, command, arg0, arg1, data_length, data_check, magic):
        """
        @param command: command identifier constant
        @param arg0: first argument
        @param arg1: second argument
        @param length: length of payload (0 is allowed)
        @param data_check: checksum of data payload
        @param magic: command ^ 0xffffffff
        """
        self.command = command
        self.arg0 = arg0
        self.arg1 = arg1
        self.data_length = data_length
        self.data_check = data_check
        self.magic = magic

        self.data = ''

    def data_received(self, data):
        self.data += data

    def __str__(self):
        """Return a packed string
        """
        msg = self
        struct.pack('5L', msg.command, msg.arg0, msg.arg1, msg.data_length,
                    msg.data_check, msg.magic)

class AdbClientProtocol(protocol.Protocol):
    deferred = None
    buff = ''

    def send_request(self, data):
        assert not self.deferred, "Can only handle one request at a time"
        self.deferred = defer.Deferred()
        self.buff = ''
        request = "%0.4X%s" % (len(data), data)
        self.transport.write(request)
        return self.deferred

    def dataReceived(self, data):
        if self.request:

    def getResponse(self, data):
        b = self.buff
        b.append(data)
        if len(b) >= 8:
            r, l, d = b[:4], b[4:8], b[8:]
            if self.buff.startswith('OKAY'):
                self.dataReceived = self.getResult
                self.dataReceived(self.buff[4:])
            elif self.buff.startswith('FAIL'):
                self.request_failed(reason)

    def request_succeded(self, data):
        pass

    def request_failed(self, reason):
        pass

endpoint = clientFromString(reactor, "tcp:localhost:5037")
factory = ClientFactory()
factory.protocol = AdbClientProtocol
client_d = endpoint.connect(factory)
@client_d.addCallback
def send_version(client):
    return client.send_request('host:version')
