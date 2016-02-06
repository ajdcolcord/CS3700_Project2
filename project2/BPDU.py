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

    def is_incoming_BPDU_better(self, BPDU_in):
        result = True
        if self.root < BPDU_in.root:
            result = False
        elif self.root == BPDU_in.root:
            if self.cost < BPDU_in.cost:
                result = False
            elif self.cost == BPDU_in.cost:
                if self.id < BPDU_in.id:
                    result = False
        return result


def create_BPDU_from_json(json_message):
    json_obj = json.loads(json_message)
    if json_obj['type'] == 'bpdu':
        src = json_obj['source']
        dest = json_obj['dest']

        message_obj = json_obj['message']
        bpdu_id = message_obj['id']
        root_id = message_obj['root']
        cost = message_obj['cost']

        return BPDU(src, dest, bpdu_id, root_id, cost)
    else:
        return False
