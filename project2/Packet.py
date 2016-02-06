#!/usr/bin/python -u
import sys
import json


class Packet():
    def __init__(self, message):
        self._parse_to_Packet(message)

    def _parse_to_Packet(self, message):
        json_message = json.loads(message)
        self.source = json_message['source']
        self.dest = json_message['dest']
        self.type = json_message['type']
        self.message = json_message['message']
        if self.message:
            self._parse_packet_message(json_message)
        print "Source: ", json_message['source']
        print "Dest: ", json_message['dest']
        print "Type: ", json_message['type']
        print "Message: ", json_message['message']

    def _parse_packet_message(self, message):
        json_message = json.loads(message)
        self.message_id = message['id']
        message_root = ""
        message_cost = ""
        if json_message['root']:
            self.message_root = message['root']
        if json_message['cost']:
            self.message_cost = message['cost']
