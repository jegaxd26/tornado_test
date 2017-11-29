from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen
import struct
import app.constants as constants
from app.utils import bxor
from app import storage

class Consul(TCPServer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        storage['listeners'] = dict()
        
    @gen.coroutine
    def handle_stream(self, stream, address):
        if address not in storage['listeners']:
            yield stream.write(self.list_connections)
            storage['listeners'][address] = stream
        while True:
            try:
                data = yield stream.read_bytes(21)
                yield stream.write(b'')
            except StreamClosedError:
                if address in storage['listeners']:
                    del storage['listeners'][address]
                break

    @property
    def list_connections(self):
        res = ''
        for a,device in storage['devices'].items():
            res = '%s|%s|%s\r\n'%(device['d_id'],device['m_id'], device['state'])
            
        return bytes(res,'ascii')

    @gen.coroutine
    def notify_clients(self,message):
        print(storage['listeners'])
        for a,c in storage['listeners'].items():
            yield c.write(message)

    
