# -*- coding: utf-8 -*-

import struct

from tornado.tcpserver import TCPServer
from tornado.ioloop import IOLoop

COLORS = {'red': 0xff0000, 'blue': 0x0000ff, 'green': 0x00ff00}
TLV = {
    'ON': {'type': 0x12, 'length': 0},
    'OFF': {'type': 0x13, 'length': 0},
    'COLOR': {'type': 0x20, 'length': 3, 'value': COLORS},
    }


def pack_command(command, value=None):
    command = TLV[command]
    pat = '>BBB' + 'B' * command['length']
    if command['length'] and value:
        values = [value // 256 ** i % 256 for i in reversed(xrange(command['length']))]
    else:
        values = []
    to_pack = [command['type'], command['length']/10, command['length']] + values
    return struct.pack(pat, *to_pack)


class FlashLightConnection(object):

    def __init__(self, stream, address, flashlights={}):
        self.stream = stream
        self.address = address
        self.flash = flashlights[str(address[1])] = {'status': None, 'color': None, 'send': self.send, 'ip': address[0]}
        self.flashlights = flashlights

        self.stream.set_close_callback(self._on_close)
        self.stream.read_until('\n', self._on_read)

    def send(self, command, value=None):
        #if not self.stream.reading():
        self.stream.write(pack_command(command, value))

    def _read(self):
        self.stream.read_until('\n', self._on_read)

    def _on_read(self, data):
        self.flash['status'] = data[:4].replace(' ', '')
        self.flash['color'] = data[4:]
        self._read()

    def _on_close(self):
        del self.flashlights[str(self.address[1])]


class FlashLightServ(TCPServer):

    def __init__(self, io_loop=None, ssl_options=None, **kwargs):
        self.flashlights = kwargs.pop('flashlights', {})
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)

    def handle_stream(self, stream, address):
        FlashLightConnection(stream, address, self.flashlights)


def main():
    server = FlashLightServ()
    server.listen(9999)


if __name__ == '__main__':
    main()
    IOLoop.instance().start()
