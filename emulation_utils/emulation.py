# -*- coding:utf-8 -*-
#!/usr/bin/env python

from tornado.ioloop import IOLoop

from http_server import main
from tcp_server import FlashLightServ


def emulation():
    flashlights = {}
    main(flashlights)
    server = FlashLightServ(flashlights=flashlights)
    server.listen(9999)

if __name__ == '__main__':
    emulation()
    IOLoop.instance().start()