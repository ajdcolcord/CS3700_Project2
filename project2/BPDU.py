#!/usr/bin/python -u
import json


class BPDU:
    def __init__(self, source, dest, ID, root, cost):
        self.source = source
        self.dest = dest
        self.type = 'bpdu'
        self.id = ID
        self.root = root
        self.cost = cost

    def create_json_BPDU(self):
        """
        Creates a BPDU in JSON based on this BPDU's information
        @return JSON object - BPDU message
        """
        json_BPDU_object = {}
        json_BPDU_object['source'] = self.source
        json_BPDU_object['dest'] = self.dest
        json_BPDU_object['type'] = 'bpdu'

        BPDU_message_object = {}
        BPDU_message_object['id'] = self.id
        BPDU_message_object['root'] = self.root
        BPDU_message_object['cost'] = self.cost

        json_BPDU_object['message'] = BPDU_message_object

        return json.dumps(json_BPDU_object)
