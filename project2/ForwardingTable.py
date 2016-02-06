#!/usr/bin/python -u
import sys


class ForwardingTable():
    def __init__(self):
        self.ports = {}

    def add_address(address, port, age):
        self.address_ports[address] = port
