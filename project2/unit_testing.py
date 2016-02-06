#!/usr/bin/env python

import unittest
import json
from Bridge import Bridge
from Packet import Packet
from ForwardingTable import ForwardingTable
from BPDU import BPDU, create_BPDU_from_json


class TestBPDUMethods(unittest.TestCase):

    json_BPDU = '{"source":"02a1", "dest":"ffff", "type": "bpdu", "message":{"id":"92b4", "root":"02a1", "cost":3}}'

    def test_create_BPDU_from_json(self):
        testBPDU = create_BPDU_from_json(self.json_BPDU)
        self.assertEquals(testBPDU.source, '02a1')
        self.assertEquals(testBPDU.dest, 'ffff')
        self.assertEquals(testBPDU.type, 'bpdu')
        self.assertEquals(testBPDU.id, '92b4')
        self.assertEquals(testBPDU.root, '02a1')
        self.assertEquals(testBPDU.cost, 3)

    def test_init_and_create_json_BPDU(self):
        testBPDU = BPDU('0ab2', 'ffff', '98b2', '0ab2', 4)
        self.assertEquals(testBPDU.source, '0ab2')
        self.assertEquals(testBPDU.dest, 'ffff')
        self.assertEquals(testBPDU.type, 'bpdu')
        self.assertEquals(testBPDU.id, '98b2')
        self.assertEquals(testBPDU.root, '0ab2')
        self.assertEquals(testBPDU.cost, 4)

        json_test_message = testBPDU.create_json_BPDU()
        json_loaded_message = json.loads(json_test_message)
        #print json_test_message

        self.assertEquals(json_loaded_message['source'], testBPDU.source)
        self.assertEquals(json_loaded_message['dest'], testBPDU.dest)
        self.assertEquals(json_loaded_message['type'], testBPDU.type)
        self.assertEquals(json_loaded_message['message']['id'], testBPDU.id)
        self.assertEquals(json_loaded_message['message']['root'], testBPDU.root)
        self.assertEquals(json_loaded_message['message']['cost'], testBPDU.cost)


if __name__ == '__main__':
    unittest.main()
