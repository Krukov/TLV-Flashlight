# -*- coding: utf-8 -*-

import socket
import sys
import signal
import logging

from tornado.ioloop import IOLoop
from tornado.iostream import IOStream


COLORS = {'red': 0xff0000, 'blue': 0x0000ff, 'green': 0x00ff00}


class Flashlight(object):
    REV_COLORS = {val: key for key, val in COLORS.items()}

    def __init__(self, status='OFF', host='127.0.0.1', port=9999):
        self.status = status
        self.host = host
        self.port = port
        self.color = '#ffffff'
        self._null_command()

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stream = IOStream(s)
        self.stream.connect((self.host, self.port), self._callback)
        self.stream.reading()
        logging.info('Connected to the server: {} {}'.format(self.host, self.port))
        IOLoop.instance().start()

    def close_connection(self):
        self.stream.close()
        IOLoop.instance().stop()

    def on(self):
        self.status = 'ON'
        logging.info('Status changed to {status}'.format(self.status))

    def off(self):
        self.status = 'OFF'
        logging.info('Status changed to {status}'.format(self.status))
        self.close_connection()
        sys.exit()

    def ch_color(self):
        value = char_sec_to_int(self.command[3:])
        rgb = '#{}'.format(hex(value)[2:])
        self.color = rgb
        logging.info('Switched to {color}'.format(self.color))

    def _callback(self):
        self.stream.read_bytes(1, self._collect_command)

    def _null_command(self):
        self.command = []
        self.length = None

    def _collect_command(self, data):
        self.command.append(data)
        if len(self.command) == 3:
            self.length = char_sec_to_int(self.command[1:3])
            print 'len = ', self.length
        elif self.length:
            self.length -= 1
        if not self.length and len(self.command) >= 3:
            self._run_command()
        self._callback()

    def _run_command(self):
        TLV[ord(self.command[0])]['callback'](self)
        print self.status
        self._null_command()


def char_sec_to_int(sec):
    return sum(ord(dig) * (256**index) for index, dig in enumerate(reversed(sec)))

TLV = {
    0x12: {'type': 'ON', 'length': 0, 'callback': Flashlight.on},
    0x13: {'type': 'OFF', 'length': 0, 'callback': Flashlight.off},
    0x20: {'type': 'COLOR', 'length': 3, 'callback': Flashlight.ch_color},
    }


if __name__ == '__main__':
    flash = Flashlight()
    signal.signal(signal.SIGINT, flash.close_connection)

    flash.connect()
