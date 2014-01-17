# -*- coding: utf-8 -*-

import socket
import datetime
import signal
import logging

from collections import defaultdict

from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado import autoreload


COLORS = {'red': 0xff0000, 'blue': 0x0000ff, 'green': 0x00ff00}


class Flashlight(object):
    """
    TCP клиент фонарика
    принимает TLV комманды от :host :port и выполняет метод
    Словарь TLV выполняет функцию роутера команда -> метод для вызова
    """

    def __init__(self, status='OFF', host='127.0.0.1', port=9999, timeout=2):
        self.status = status
        self.host = host
        self.port = port
        self.timeout = datetime.timedelta(seconds=timeout)
        self._init_time = datetime.datetime.now()
        self.color = '#ffffff'
        self._clear_command()

    def connect(self):
        logging.info('Connecting to the server: {} {}'.format(self.host, self.port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stream = IOStream(s)
        self.stream.set_close_callback(self._on_close)
        self.stream.connect((self.host, self.port), self._on_connect)
        IOLoop.instance().start()
        if self.stream.closed():
            logging.error("Can't connect to {} {}".format(self.host, self.port))

    def close_connection(self):
        self.stream.close()
        IOLoop.instance().stop()
        IOLoop.instance().close()

    def on(self):
        self.status = 'ON'
        logging.info('Status changed to {status}'.format(status=self.status))
        self.send_status()

    def off(self):
        self.status = 'OFF'
        logging.info('Status changed to {status}'.format(status=self.status))
        self.send_status()

    def ch_color(self):
        value = char_sec_to_int(self.command[3:])
        rgb = '#{}'.format(hex(value)[2:])
        self.color = rgb
        logging.info('Switched to {color}'.format(color=self.color))
        self.send_status()

    def send_status(self, callback=None):
        if not self.stream.reading():
            self.stream.write('{:<4}{}\n'.format(self.status, self.color), callback=callback)

    def _on_close(self):
        self.close_connection()

    def _on_connect(self):
        self._callback()

    def _callback(self):
        self.stream.read_bytes(1, self._collect_command)

    def _clear_command(self):
        self.command = []
        self.length = 0

    def _collect_command(self, data):
        self.command.append(data)
        if len(self.command) == 3:
            self.length = char_sec_to_int(self.command[1:3])
        elif self.length:
            self.length -= 1
        if not self.length and len(self.command) >= 3:
            self._run_command()
        self._callback()

    def _run_command(self):
        TLV[ord(self.command[0])]['callback'](self)
        self._clear_command()


def char_sec_to_int(sec):
    return sum(ord(dig) * (256**index) for index, dig in enumerate(reversed(sec)))


S_TLV = {
    0x12: {'type': 'ON', 'length': 0, 'callback': Flashlight.on},
    0x13: {'type': 'OFF', 'length': 0, 'callback': Flashlight.off},
    0x20: {'type': 'COLOR', 'length': 3, 'callback': Flashlight.ch_color},
    }
TLV = defaultdict(lambda: defaultdict(dict))
TLV.update(**{key: defaultdict(None, **value) for key, value in S_TLV.iteritems()})


if __name__ == '__main__':
    flash = Flashlight()
    signal.signal(signal.SIGINT, flash.close_connection)

    flash.connect()
