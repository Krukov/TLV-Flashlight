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

def hex_to_str(num):
    bin_form = bin(num)[2:]
    return ''.join([chr(int(bin_form[i*8:i*8+8], 2)) for i in range(len(bin_form)/8)])


def tlv_command(name, value=None):
    resp = TLV[name]
    value = hex_to_str(value) if value else ''
    length = ''.join((chr(int(i)) for i in '{:0>2}'.format(resp['length'])))
    command = b'{type}{length}{value}'.format(type=chr(resp['type']), length=length, value=value)
    return command


class FlashLightConnection(object):

    def __init__(self, stream, address, flashlights={}):
        self.stream = stream
        self.address = address
        self.flash = flashlights[str(address[1])] = {'status': None, 'color': None, 'send': self.send, 'ip': address[0]}
        self.flashlights = flashlights

        self.stream.set_close_callback(self._on_close)
        self.stream.read_until('\n', self._on_read)
        self.stream.reading()

    def send(self, command, value=None):
        self.stream.write(tlv_command(command, value))

    def _on_read(self, data):
        self.flash['status'] = data[:4].replace(' ', '')
        self.flash['color'] = data[4:]

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
