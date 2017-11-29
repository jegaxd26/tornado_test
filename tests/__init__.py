import unittest
from app import run
import threading
import socket
import time

import struct
import app.constants as constants
from app.utils import bxor
import select

class Device(object):
    def __init__(self):
        self.message_number=1
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('127.0.0.1',8888))
        
    def send_message(self,message):
        self.message_number += 1
        self.socket.send(message)
        return self.socket.recv(4)
    
    def shutdown(self):
        self.socket.close()
        
class Observer(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('127.0.0.1',8889))
        self.socket.setblocking(0)
        self.timeout = 1


        self.devices = []
        devices = self.read_queue()
        if devices:
            # split creates last element that is empty
            self.devices = devices.decode('ascii').split('\r\n')[:-1]
    def read_queue(self):
        data = b''
        ready = select.select([self.socket], [], [], self.timeout)
        if ready[0]:
            try:
                while True:
                    chunk = self.socket.recv(1)
                    if not chunk: break
                    data += chunk
            except socket.error as err:
                pass
        return data
                
    def disconnect(self):
        self.socket.close()
        
class BasicTest(unittest.TestCase):
    def setUp(self):
        storage = dict()
        
    @classmethod
    def setUpClass(cls):
        def run_app():
            run()
        cls.app_thread = threading.Thread(target=run_app)
        cls.app_thread.start()
        time.sleep(1)
        
    def test_collector(self):
        device_1 = Device()
        string = struct.pack('=BH8sBB8sL',constants.FIRST_BYTE,device_1.message_number,bytes('device_1','ascii'),
                             constants.ACTIVE,0x1,bytes('lola','ascii'),13213)
        checksum = bxor(string)
        string += checksum
        response = device_1.send_message(string)
        (header,message_number,checksum) = struct.unpack('=BHc',response)
        
        assert header == 0x11 # success header
        assert message_number == 1
        assert checksum == bxor(struct.pack('=BH',header,message_number))

        string = struct.pack('=BH8sBB8sL8sL',constants.FIRST_BYTE,device_1.message_number,bytes('device_1','ascii'),
                             constants.ACTIVE,0x2,bytes('lola','ascii'),13213,bytes('lola2','ascii'),123)
        checksum = bxor(string)
        string += checksum
        response = device_1.send_message(string)
        (header,message_number,checksum) = struct.unpack('=BHc',response)
        
        assert header == 0x11 # success header
        assert message_number == 2
        assert checksum == bxor(struct.pack('=BH',header,message_number))

        #string = b'a'*21
        #response = device_1.send_message(string)
        #(header,message_number,checksum) = struct.unpack('=BHc',response)
        
        string = struct.pack('=BH8sBB8sL',constants.FIRST_BYTE,device_1.message_number,bytes('device_1','ascii'),
                             constants.ACTIVE,0x1,bytes('lola','ascii'),13213)
        checksum = b'1'
        string += checksum
        response = device_1.send_message(string)
        (header,message_number,checksum) = struct.unpack('=BHc',response)
        
        assert header == 0x12 # success header
        assert message_number == 0
        assert checksum == bxor(struct.pack('=BH',header,message_number))
        
        device_2 = Device()
        string = struct.pack('=BH8sBB8sL',constants.FIRST_BYTE,device_2.message_number,bytes('device_2','ascii'),
                             constants.ACTIVE,0x1,bytes('lola','ascii'),13213)
        checksum = bxor(string)
        string += checksum
        response = device_2.send_message(string)
        (header,message_number,checksum) = struct.unpack('=BHc',response)
        
        assert header == 0x11 # success header
        assert message_number == 1
        assert checksum == bxor(struct.pack('=BH',header,message_number))

        device_1.shutdown()
        device_2.shutdown()

        
    def test_observer(self):
        device_1 = Device()
        device_2 = Device()

        string = struct.pack('=BH8sBB8sL',constants.FIRST_BYTE,device_1.message_number,bytes('device_1','ascii'),
                             constants.ACTIVE,0x1,bytes('lola','ascii'),0)
        checksum = bxor(string)
        string += checksum
        device_1.send_message(string)
        
        string = struct.pack('=BH8sBB8sL8sL',constants.FIRST_BYTE,device_1.message_number,bytes('device_1','ascii'),
                             constants.ACTIVE,0x2,bytes('lola','ascii'),1,bytes('lola2','ascii'),2)
        checksum = bxor(string)
        string += checksum
        device_1.send_message(string)

        observer_1 = Observer()
        assert len(observer_1.devices) == 1

        string = struct.pack('=BH8sBB8sL8sL',constants.FIRST_BYTE,device_2.message_number,bytes('device_2','ascii'),
                             constants.ACTIVE,0x2,bytes('a','ascii'),1,bytes('b','ascii'),2)
        checksum = bxor(string)
        string += checksum
        device_2.send_message(string)

        observer_2 = Observer()
        assert len(observer_2.devices) == 2

        string = struct.pack('=BH8sBB8sL8sL',constants.FIRST_BYTE,device_2.message_number,bytes('device_2','ascii'),
                             constants.ACTIVE,0x2,bytes('a','ascii'),0,bytes('b','ascii'),1)
        checksum = bxor(string)
        string += checksum
        device_2.send_message(string)

        response_1 = observer_1.read_queue().decode('ascii').split('\r\n')[:-1]
        response_2 = observer_2.read_queue().decode('ascii').split('\r\n')[:-1]

        assert len(response_1) == 4
        assert len(response_2) == 2

        assert response_1[-1] == response_2[-1]

        observer_1.disconnect()
        observer_2.disconnect()
        
        
    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
