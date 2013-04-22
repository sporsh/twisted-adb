"""
@author: Geir Sporsheim
@see: git repo https://android.googlesource.com/platform/system/core/
@see: source file adb/adb.h
"""

from twisted.internet import protocol
import struct
import logging

log = logging.getLogger()

VERSION = 0x01000000  # ADB protocol version
MAX_PAYLOAD = 4096

# Message command constants
CMD_SYNC = 0x434e5953
CMD_CNXN = 0x4e584e43
CMD_OPEN = 0x4e45504f
CMD_OKAY = 0x59414b4f
CMD_CLSE = 0x45534c43
CMD_WRTE = 0x45545257

def getCommandString(commandCode):
    """Returns a readable string representation of a message code
    """
    return struct.pack('<L', commandCode)


class AdbProtocolBase(protocol.Protocol):
    version = VERSION
    maxPayload = MAX_PAYLOAD

    def __init__(self):
        self.buff = ''
        self.streams = {}
        self.messageHandler = self

    def dataReceived(self, data):
        self.buff += data
        message = self.getMessage()
        while message:
            self.dispatchMessage(message)
            message = self.getMessage()

    def getMessage(self):
        try:
            message, self.buff = AdbMessage.decode(self.buff)
        except:
            #TODO: correctly handle corrupt messages
            return
        return message

    def dispatchMessage(self, message):
        name = 'handle_' + getCommandString(message.command)
        handler = getattr(self.messageHandler, name, self.unhandledMessage)
        handler(message.arg0, message.arg1, message.data)

    def unhandledMessage(self, message):
        log.debug("Unhandled message: %s", message)

    def sendCommand(self, command, arg0, arg1, data):
        #TODO: split data into chunks of MAX_PAYLOAD
        message = AdbMessage(command, arg0, arg1, data + '\x00')
        self.transport.write(message.encode())

    def send_CNXN(self, systemType, serialNumber='', banner=''):
        """Connect to the remote, giving our system information

        @param systemType: "bootloader", "device" or "host"
        @param serialNumber: Some kind of unique ID (or empty)
        @param banner: Human-readable version or identifier string.
                       The banner is used to transmit useful properties.
        """
        systemIdentityString = ':'.join((systemType, serialNumber, banner))
        self.sendCommand(CMD_CNXN,
                         self.version,
                         self.maxPayload,
                         systemIdentityString)

    def handle_CNXN(self, version, maxPayload, systemIdentityString):
        """Called when we get an incoming CNXN message
        """
        if version != self.version or maxPayload < maxPayload:
            self.transport.loseConnection()
        else:
            self.connectSession(systemIdentityString)

    def connectSession(self, systemIdentityString):
        raise NotImplementedError()

    def handle_OPEN(self, remoteId, sessionId, destination):
        localId = len(self.streams)
        self.streams[localId] = self.openStream(destination)

    def handle_OKAY(self, remoteId, localId, data):
        """Called when the remote side has opened a stream
        """
        stream = self.streams[localId]
        stream.open(remoteId)

    def openStream(self, destination):
        raise NotImplementedError()

    def handle_CLSE(self, remoteId, localId, data):
        self.closeStream(localId)

    def closeStream(self, localId):
        remoteId = self.streams.get(localId, None)
        if not remoteId is None:
            self.sendCommand(CMD_CLSE, localId, remoteId, "")
            self.streams[localId] = None

    def streamWrite(self, remoteId, data):
        """Write data to a stream
        """
        self.sendCommand(CMD_WRTE, 0, remoteId, data)


class AdbMessage(object):
    def __init__(self, command, arg0, arg1, data=''):
        self.command = command
        self.arg0 = arg0
        self.arg1 = arg1
        self.data = data

    @property
    def header(self):
        data_check = sum(ord(c) for c in self.data)
        magic = self.command ^ 0xffffffff
        return AdbMessageHeader(self.command,
                                self.arg0,
                                self.arg1,
                                len(self.data),
                                data_check,
                                magic)

    @classmethod
    def decode(cls, data):
        header, data = AdbMessageHeader.decode(data)
        if len(data) < header.data_length:
            return
        message = cls(header.command, header.arg0, header.arg1, data)
        message.validate(header)
        return message, data[header.data_length:]

    def encode(self):
        return self.header.encode() + self.data

    def validate(self, header):
        assert self.header == header

    def __eq__(self, other):
        return self.header == other.header and self.data == other.data

    def __repr__(self):
        return "%s(%r)" % (self.header, self.data)


class AdbMessageHeader(tuple):
    _fmt = '<6L'

    def __new__(cls, command, arg0, arg1, data_length, data_check, magic):
        """
        @param command: command identifier constant
        @param arg0: first argument
        @param arg1: second argument
        @param length: length of payload (0 is allowed)
        @param data_check: checksum of data payload
        @param magic: command ^ 0xffffffff
        """
        return tuple.__new__(cls, (command,
                                   arg0,
                                   arg1,
                                   data_length,
                                   data_check,
                                   magic))

    command = property(lambda self: self[0])
    arg0 = property(lambda self: self[1])
    arg1 = property(lambda self: self[2])
    data_length = property(lambda self: self[3])
    data_check = property(lambda self: self[4])
    magic = property(lambda self: self[5])

    def encode(self):
        return struct.pack(self._fmt,
                           self.command,
                           self.arg0,
                           self.arg1,
                           self.data_length,
                           self.data_check,
                           self.magic)

    @classmethod
    def decode(cls, data):
        length = struct.calcsize(cls._fmt)
        if len(data) < length:
            return
        args = struct.unpack(cls._fmt, data[:length])
        return cls(*args), data[length:]

    def __str__(self, *args, **kwargs):
        return str((getCommandString(self.command),
                   self.arg0, self.arg1, self.data_length,
                   self.data_check, self.magic))
