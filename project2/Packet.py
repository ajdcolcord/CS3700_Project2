#!/usr/bin/python -u
import sys
import json


class Packet():
    def __init__(self, message):
        _parse_to_Packet(message)

    def _parse_to_Packet(message):
        json_message = json.loads(message)
        self.source = json_message['source']
        self.dest = json_message['dest']
        self.type = json_message['type']
        self.message = json_message['message']
        if self.message:
            _parse_packet_message(packet_message)
        print "Source: ", json_message['source']
        print "Dest: ", json_message['dest']
        print "Type: ", json_message['type']
        print "Message: ", json_message['message']

    def _parse_packet_message(message):
        packet_message = json.loads(message)
        self.message_id = message['id']
        message_root = ""
        message_cost = ""
        if packet_message['root']:
            self.message_root = message['root']
        if packet_message['cost']:
            self.message_cost = message['cost']
