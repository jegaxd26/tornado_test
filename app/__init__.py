storage = dict() # FIXME not beautiful

import tornado.ioloop
from app.modules import Collector, Consul
#from tornado.log import enable_pretty_logging


def run():
    #enable_pretty_logging()
    consul = Consul()
    
    def callback(message):
        consul.notify_clients(message)
        
    collector = Collector(message_callback=callback)

    consul.listen(8889)
    collector.listen(8888)
    
    tornado.ioloop.IOLoop.current().start()
