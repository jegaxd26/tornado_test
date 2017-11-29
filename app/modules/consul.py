from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen
import struct
import app.constants as constants
from app import storage
import time

class Consul(TCPServer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        storage['observers'] = dict()
        
    @gen.coroutine
    def handle_stream(self, stream, address):
        if address not in storage['observers']:
            yield stream.write(self.list_connections)
            storage['observers'][address] = stream
        while True:
            try:
                # also best effort, since we have no delimiter.
                yield stream.read_bytes(21)
            except StreamClosedError:
                if address in storage['observers']:
                    del storage['observers'][address]
                break

    @property
    def list_connections(self):
        res = ''
        for a,device in storage['devices'].items():
            res += '%s|%s|%s|%s\r\n'%(device['d_id'],device['m_id'],device['state'],int((time.time()-device['last_message'])*1000))
        return bytes(res,'ascii')

    @gen.coroutine
    def notify_clients(self,message):
        for a,c in storage['observers'].items():
            yield c.write(message)

    
