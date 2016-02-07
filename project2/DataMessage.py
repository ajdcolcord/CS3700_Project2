#!/usr/bin/python -u
import json


class DataMessage:
    def __init__(self, source, dest, ID, cost):
        self.source = source
        self.dest = dest
        self.type = 'data'
        self.id = ID
        self.timeout = None

    def create_json_DataMessage(self):
        """
        Creates a DataMessage in JSON based on this DataMessage's information
        @return JSON object - DataMessage message
        """
        json_DataMessage_object = {}
        json_DataMessage_object['source'] = self.source
        json_DataMessage_object['dest'] = self.dest
        json_DataMessage_object['type'] = 'bpdu'

        DataMessage_message_object = {}
        DataMessage_message_object['id'] = self.id
        DataMessage_message_object['root'] = self.root
        DataMessage_message_object['cost'] = self.cost

        json_DataMessage_object['message'] = DataMessage_message_object

        return json.dumps(json_DataMessage_object)


def create_DataMessage_from_json(json_message):
    json_obj = json.loads(json_message)
    if json_obj['type'] == 'bpdu':
        src = json_obj['source']
        dest = json_obj['dest']

        message_obj = json_obj['message']
        datamessage_id = message_obj['id']

        return DataMessage(src, dest, datamessage_id)
    else:
        return False
