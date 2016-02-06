#!/usr/bin/python -u
import sys


class ForwardingTable():
    def __init__(self):
        self.ports = {}

    def add_address(address, port, age):
        self.ports[address] = port

    # def new_message_arrived
    # if destination in ports: send message on port
    # if destination not in ports: broadcast to all ports except incoming port
    
