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
        message = AdbMessage(command, arg0, arg1, data)
        self.transport.write(message.encode())

    def connectSession(self, systemType, serialNumber='', banner=''):
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
                         systemIdentityString + '\x00')

    def handle_CNXN(self, version, maxPayload, systemIdentityString):
        """Called when we get an incoming CNXN message
        """
        if version != self.version or maxPayload < maxPayload:
            log.error("Disconnecting: Protocol version or max payload mismatch")
            self.transport.loseConnection()
        else:
            self.sessionConnected(systemIdentityString)

    def sessionConnected(self, systemIdentityString):
        """On servers, this is called after we receive a valid CNXN message
        from a client.
        On clients, this is called when the server has replied to our CNXN
        """
        raise NotImplementedError()

    def openStream(self, stream):
        localId = len(self.streams) + 1
        self.streams[localId] = stream
        stream.localId = localId
        self.sendCommand(CMD_OPEN,
                         stream.localId,
                         0,
                         stream.destination + '\x00')

    def handle_OPEN(self, remoteId, sessionId, destination):
        """Called when we receive a message indicating that the other side
        has a stream identified by :remoteId: that it wishes to connect to
        the named :destination: on our side.

        We reply to this message with either a OKAY, indicating the connection
        has been established, or a CLSE message indicating failure.

        An OPEN message implies an OKAY message from the connecting remote stream.
        """
        localId = len(self.streams) + 1
        try:
            assert remoteId != 0, "stream id can not be 0"
            stream = self.openStream(destination)
            self.streams[localId] = stream
        except:
            log.exception("could not open stream")
            # Indicate that the open failed
            self.sendCommand(CMD_CLSE, 0, remoteId, '')
        else:
            # Indicate that the connection has been established
            self.sendCommand(CMD_OKAY, localId, remoteId, '')
            # Handle implicit OKAY message for the stream
            stream.open(remoteId)

    def handle_OKAY(self, remoteId, localId, data):
        """Called when the stream on the remote side is ready for write.
        @param data: should be ""
        """
        if not (remoteId and localId):
            raise AdbError("Neither the local-id nor the"
                           "remote-id may be zero.")
        self.streamOpened(remoteId, localId)

    def streamOpened(self, remoteId, localId):
        print "STREAM OPENED"
        stream = self.streams[localId]
        stream.ready(remoteId)

    def closeStream(self, localId, remoteId):
        self.sendCommand(CMD_CLSE,
                         localId,
                         remoteId,
                         '')

    def handle_CLSE(self, remoteId, localId, data):
        self.streamClosed(localId)

    def streamClosed(self, localId):
        """Called when the remote side wants to close a stream
        """
        stream = self.streams.get(localId, None)
        print "STREAM: %r" % stream
        if stream:
            self.streams[localId] = None
            stream.close("Stream closed cleanly.")

    def streamWrite(self, remoteId, data):
        """Write data to a stream
        """
        self.sendCommand(CMD_WRTE, 0, remoteId, data)

    def handle_WRTE(self, remoteId, localId, data):
        stream = self.streams.get(localId, None)
        if stream:
            stream.protocol.dataReceived(data)
            self.sendCommand(CMD_OKAY,
                             localId,
                             remoteId,
                             '')


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
