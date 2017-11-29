import unittest
from datetime import datetime
from app import run
import socket

class BasicTest(unittest.TestCase):
    def setUp(self):
        self.COLLECTOR_PORT = 8888
        self.CONSUL_PORT = 8889
        self.BUFFER_SIZE = 1024

    def tearDown(self):
        pass

