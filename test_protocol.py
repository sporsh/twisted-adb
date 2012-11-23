import unittest
import client

class AdbProtocolTest(unittest.TestCase):
    def setUp(self):
        self.protocol = client.AdbProtocolBase()

    def test_get_message(self):
        messages = []
        self.protocol.adb_OKAY = messages.append

        data = "hello adb\x00"
        message = client.AdbMessage(client.A_OKAY, 0, 1, data)
        # Encode the message and send it in two pieces
        encoded_message = message.encode()
        self.protocol.dataReceived(encoded_message[:10])
        self.protocol.dataReceived(encoded_message[10:])

        self.assertEqual(messages, [message])

    def test_encode_decode_message(self):
        # This is the connect message grabbed from adb server
        data = ('\x43\x4e\x58\x4e\x00\x00\x00\x01'
                '\x00\x10\x00\x00\x07\x00\x00\x00'
                '\x32\x02\x00\x00\xbc\xb1\xa7\xb1'
                '\x68\x6f\x73\x74\x3a\x3a\x00')

        message = client.AdbMessage(client.A_CNXN,
                                    client.A_VERSION,
                                    client.MAX_PAYLOAD,
                                    'host::\x00')

        self.assertEquals(message.encode(), data,
                          "Message did encode to the expected data")

        decoded_message, _ = client.AdbMessage.decode(data)
        self.assertEquals(decoded_message, message,
                          "Data did not decode to the expected message")
