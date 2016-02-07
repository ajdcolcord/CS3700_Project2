#!/usr/bin/env python

import unittest
import json
from Bridge import Bridge
from Packet import Packet
from ForwardingTable import ForwardingTable
from BPDU import BPDU, create_BPDU_from_json
from DataMessage import DataMessage, create_DataMessage_from_json


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
        self.assertEquals(json_loaded_message['source'], testBPDU.source)
        self.assertEquals(json_loaded_message['dest'], testBPDU.dest)
        self.assertEquals(json_loaded_message['type'], testBPDU.type)
        self.assertEquals(json_loaded_message['message']['id'], testBPDU.id)
        self.assertEquals(json_loaded_message['message']['root'], testBPDU.root)
        self.assertEquals(json_loaded_message['message']['cost'], testBPDU.cost)

    def test_is_incoming_BPDU_better(self):
        testBPDU1 = BPDU('0ab2', 'ffff', '98b2', '0ab2', 4)
        testBPDU2 = BPDU('91b5', 'ffff', '98b3', '0ab2', 4)
        testBPDU3 = BPDU('0ab2', 'ffff', '98b2', '0ab5', 4)
        testBPDU4 = BPDU('0ab2', 'ffff', '98b2', '0ab2', 6)

        self.assertFalse(testBPDU1.is_incoming_BPDU_better(testBPDU2))
        self.assertFalse(testBPDU1.is_incoming_BPDU_better(testBPDU3))
        self.assertFalse(testBPDU1.is_incoming_BPDU_better(testBPDU4))
        self.assertTrue(testBPDU4.is_incoming_BPDU_better(testBPDU1))


class TestDataMessageMethods(unittest.TestCase):
    json_Data = '{"source":"02a1", "dest":"9xa2", "type": "data", "message":{"id":"92b4"}}'

    def test_create_DataMessage_from_json(self):
        testDataMessage = create_DataMessage_from_json(self.json_Data)
        self.assertEquals(testDataMessage.source, '02a1')
        self.assertEquals(testDataMessage.dest, '9xa2')
        self.assertEquals(testDataMessage.type, 'data')
        self.assertEquals(testDataMessage.id, '92b4')

    def test_init_and_create_json_DataMessage(self):
        testDataMessage = DataMessage('02a1', '9xa2', '98b2')
        self.assertEquals(testDataMessage.source, '02a1')
        self.assertEquals(testDataMessage.dest, '9xa2')
        self.assertEquals(testDataMessage.type, 'data')
        self.assertEquals(testDataMessage.id, '98b2')

        json_test_message = testDataMessage.create_json_DataMessage()
        json_loaded_message = json.loads(json_test_message)
        self.assertEquals(json_loaded_message['source'], testDataMessage.source)
        self.assertEquals(json_loaded_message['dest'], testDataMessage.dest)
        self.assertEquals(json_loaded_message['type'], testDataMessage.type)
        self.assertEquals(json_loaded_message['message']['id'], testDataMessage.id)



if __name__ == '__main__':
    unittest.main()
