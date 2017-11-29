from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen
from tornado.testing  import gen_test
import struct
import app.constants as constants
from app.utils import bxor
from app import storage
from collections import defaultdict

class Collector(TCPServer):
    def __init__(self,*args,message_callback=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.message_callback = message_callback
        storage['devices'] = defaultdict()
        
    @gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                fail = False
                data = yield stream.read_bytes(21)
                (header,m_id,d_id,state,numfields,name) = struct.unpack(constants.PACKET_BEGINING,data)
                add_data = b''
                checksum = b''
                value = b''
                if numfields == 1:
                    add_data = yield stream.read_bytes(1)
                    (checksum) = struct.unpack(constants.PACKET_END_WITHOUT_VALUE,add_data)
                elif numfields == 2:
                    add_data = yield stream.read_bytes(5)
                    (value,checksum) = struct.unpack(constants.PACKET_END_WITH_VALUE,add_data)
                else: fail = True
                data += add_data
                new_checksum = bxor(data[:-1])
                
                if checksum != new_checksum:
                    fail = True
                    
                response = struct.pack(constants.RESPONSE_FORMAT,
                                       constants.RESPONSE_FAIL if fail else constants.RESPONSE_SUCCESS,
                                       0 if fail else m_id)
                
                checksum = bxor(response)
                response += checksum
                                       
                yield stream.write(response)

                storage['devices'][address] = dict(d_id=d_id,m_id=m_id,state=state)
                    

                if self.message_callback:
                    message = d_id+b'|'+name+b'|'+ value +b'\r\n'
                    yield self.message_callback(message)
                
            except StreamClosedError:
                break

