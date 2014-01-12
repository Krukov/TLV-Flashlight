# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os

import tornado.escape
import tornado.httpserver
import tornado.options
import tornado.web

from tornado.ioloop import IOLoop
from tornado.options import define

define("port", default=8000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self, flashlights):
        self.flashlights = flashlights
        handlers = [
            (r"/control", MainHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=True,)

        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render_page()

    def post(self):
        data = {i.split('=')[0]: i.split('=')[1] for i in self.request.body.split('&')}
        flash = self.application.flashlights[data['address']]

        if 'status' in data:
            flash['send'](data['status'])
        if 'color' in data:
            flash['send']('COLOR', value=int(data['color_val'], 16))
        self.render_page()

    def render_page(self):
        flashlights = self.application.flashlights.iteritems()
        self.render(
            "main.html",
            flashlights=flashlights,)


def main(flashlights={}):
    tornado.options.parse_command_line()
    app = Application(flashlights)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(tornado.options.options.port)


if __name__ == '__main__':
    main()
    IOLoop.instance().start()