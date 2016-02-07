#!/usr/bin/python -u
import json


class DataMessage:
    """
    This is the DataMessage class for messages that are meant to be Sent
    from host to host
    """
    def __init__(self, source, dest, ID):
        """
        This creates a new DataMessage based on the provided information
        @param source : the source address
        @param dest : the destination address
        @param ID : the message ID
        """
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
        json_DataMessage_object['type'] = 'data'

        DataMessage_message_object = {}
        DataMessage_message_object['id'] = self.id

        json_DataMessage_object['message'] = DataMessage_message_object

        return json.dumps(json_DataMessage_object)


def create_DataMessage_from_json(json_message):
    """
    This function takes in a json_message, checks if it's type is 'data',
    if so, creates a new DataMessage object from it's contained information
    @param json_message : the json message to create an object from
    @return DataMessage from the provided message's information, returns False
    if the type is not 'data'
    """
    json_obj = json.loads(json_message)
    if json_obj['type'] == 'data':
        src = json_obj['source']
        dest = json_obj['dest']

        message_obj = json_obj['message']
        datamessage_id = message_obj['id']

        return DataMessage(src, dest, datamessage_id)
    else:
        return False
