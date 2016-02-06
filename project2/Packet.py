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
        self.messageID = self.message['id']

        print "Source: ", self.source
        print "Dest: ", self.dest
        print "Type: ", self.type
        print "Message: ", self.message
        print "MessageID: ", self.messageID


    #bridge logic:
    # all bridges first assume they are the root
    # for each received BPDU, the switch chooses:
    #     - a new root (smallest known ROOT ID)
    #     - a new root port (the port that points toward that root)
    #     - a new designated bridge (who is the next hop to root)
    # DO THIS BY USING LOGIC:
    #  - if ROOT ID1 < ROOT ID2: use BPDU-1
    #  - else if ROOT ID1 == ROOT ID2 && COST1 < COST2: use BPDU-1
    #  - else if ROOT ID1 == ROOT ID2 && COST1 == COST2 && BRIDGE-ID1 < BRIDGE-ID2: use BPDU-1
    #  - else: use BPDU-2

    # BPDU logic:
    # elect root Bridge
    # locate next hop closest to root, and it's port
    # select ports to be included in spanning trees, disable others
