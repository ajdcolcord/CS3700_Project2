#!/usr/bin/python -u
import sys
import time


class ForwardingTable():
    """
    This is the class for a bridge's forwarding table, which holds a dictionary
    of addresses, each that has a tuple of a port number matched with a timeout
    """
    def __init__(self):
        """
        This creates a new forwarding table with an empty address list
        """
        self.addresses = {}

    def add_address(self, address, port):
        """
        Adds the given address to the forwarding table at the given port, or
        updates the existing entry with the new port and a new timeout
        @param address : the address to add
        @param port : the port to add
        """
        self.addresses[address] = (port, time.time())

    def get_address_port(self, address):
        """
        Returns the port number for the given address, if not timed out
        @param address : the address to find the port
        @return int : the port number for the address, or False if not found
        """
        if address in self.addresses:
            if int(round((time.time() - self.addresses[address][1]) * 1000)) > 5000:
                del self.addresses[address]
                return False
            else:
                return self.addresses[address][0]
