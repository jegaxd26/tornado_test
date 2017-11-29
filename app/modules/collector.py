from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen
import struct
import app.constants as constants
from app.utils import bxor
from app import storage
from collections import defaultdict
import time

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
                # This is best effort, the document didn't specify a delimiter for the message, so if we have 1 message that is 
                # shorter/longer than it should be or it's numfields is incorrect/coccupted it will break entire queue
                data = yield stream.read_bytes(13)
                numfields=0
                try:
                    # is it devices responsability to track message id PER connection?
                    (header,m_id,d_id,state,numfields) = struct.unpack(constants.PACKET_BEGINING,data)
                except Exception:
                    fail = True

                state_repr = ''
                if state == constants.ACTIVE:
                    state_repr='ACTIVE'
                elif state == constants.IDLE:
                    state_repr='IDLE'
                elif state == constants.RECHARGING:
                    state_repr='RECHARGING'
                else:
                    fail = True

                values = yield stream.read_bytes(numfields*(12))
                checksum = yield stream.read_bytes(1)

                data += values+checksum
                
                (checksum,) = struct.unpack(constants.PACKET_END,checksum)

                new_checksum = bxor(data[:-1])
                
                if checksum != new_checksum:
                    fail = True
                    
                if values:
                    values = {values[i:i+8]:values[i+8:i+12] for i in range(0,len(values),12)}

                response = struct.pack(constants.RESPONSE_FORMAT,
                                       constants.RESPONSE_FAIL if fail else constants.RESPONSE_SUCCESS,
                                       0 if fail else m_id)
                checksum = bxor(response)
                response += checksum
                yield stream.write(response)

                storage['devices'][address] = dict(d_id=d_id.decode('ascii'),
                                                   m_id=m_id,
                                                   state=state_repr,
                                                   last_message=time.time())
                    
                if self.message_callback:
                    message = ''
                    for field,value in values.items():
                        message += '%s|%s|%s\r\n'%(d_id.decode('ascii').rstrip('\0'),
                                                   field.decode('ascii').rstrip('\0'),
                                                   int.from_bytes(value,constants.ENDIAN))
                        
                    yield self.message_callback(bytes(message,'ascii'))
                
            except StreamClosedError:
                if address in storage['devices']:
                    del storage['devices'][address]
                break

