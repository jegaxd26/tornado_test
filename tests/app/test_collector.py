from nose.tools import *
from nose.plugins.attrib import attr
import json
from . import BasicAppTest
import threading
from tornado.testing  import AsyncTestCase, gen_test

from app.modules import Collector
import threading
from functools import partial
import uuid
import struct 
import app.constants as constants
import socket
from app.utils import bxor


@attr('collector')
class CollectorTest(AsyncTestCase,BasicAppTest):
    
    def setUp(self):
        super(CollectorTest,self).setUp()
        self.collector = Collector(port=8888,io_loop=self.io_loop)

    @attr('slow')
    @gen_test
    def test_endpoint_connection_pool(self):
        
        def test_socket():
            tsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tsocket.connect(('127.0.0.1',8888))
            seq_number = 1
            string = struct.pack('=BH8sBB8sL',constants.FIRST_BYTE,seq_number,uuid.uuid4().bytes[:8],constants.ACTIVE,0x2,bytes('lola','ascii'),13213)
            checksum = bxor(string)
            string += checksum
            tsocket.send(string)
            data = b''
            while True:
                chunk = tsocket.recv(self.BUFFER_SIZE)
                if not chunk: break
                data+=chunk
            tsocket.close()
            (header,m_id,checksum) = struct.unpack(constants.RESPONSE_FORMAT+'c',data)
            assert header == constants.RESPONSE_SUCCESS
            assert m_id == seq_number
            assert bxor(data[:-1]) == checksum
            
        threads = []
        for _ in range(10):
            threads.append(threading.Thread(target=test_socket))
        for thread in threads:
            thread.start()

        #for thread in threads:
        #    thread.join()
    

    def tearDown(self):
        super(CollectorTest,self).tearDown()
        self.collector.server.stop()
