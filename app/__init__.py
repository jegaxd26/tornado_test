storage = dict()

import tornado.ioloop
import app.modules as modules
from app.modules import Collector, Consul
from tornado.log import enable_pretty_logging


def run():
    #for module in modules.__all__:
    #    module()
    enable_pretty_logging()
    consul = Consul()
    def callback(message):
        consul.notify_clients(message)
    collector = Collector(message_callback=callback)

    consul.listen(8889)
    collector.listen(8888)
    tornado.ioloop.IOLoop.current().start()
