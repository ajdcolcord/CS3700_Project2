#!/usr/bin/python -u
import sys
import json


class Packet():
    def __init__(self, message=None):
        self._parse_to_Packet(message)
        self.isBPDU = False

    def _parse_to_Packet(self, message):
        json_message = json.loads(message)
        self.source = json_message['source']
        self.dest = json_message['dest']
        self.type = json_message['type']
        self.message = json_message['message']
        self.id = self.message['id']

        print "Source: ", self.source
        print "Dest: ", self.dest
        print "Type: ", self.type
        print "Message: ", self.message
        print "MessageID: ", self.id

        if self.type == 'bpdu':
            self._create_BPDU(self.message)
            self.isBPDU = True

    def _parse_to_BPDU(self, message):
        self.rootID = message['root']
        self.cost = message['cost']
        print "RootID: ", self.rootID
        print "Cost: ", self.cost
    '''
    def _create_new_BPDU(self, source, dest, BPDU_id, root, cost):
        self.source = source
        self.dest = dest
        self.type = 'bpdu'
        self.id = BPDU_id
        self.root = root
        self.cost = cost
    {"source":"02a1", "dest":"ffff", "type": "bpdu",
      "message":{"id":"92b4", "root":"02a1", "cost":3}}
      '''
