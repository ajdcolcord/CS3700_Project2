#!/usr/bin/python -u
import datetime


class ForwardingTable:
    """
    This is the class for a bridge's forwarding table, which holds a dictionary
    of addresses, each that has a tuple of a port number matched with a timeout
    """
    def __init__(self):
        """
        This creates a new forwarding table with an empty address list
        """
        self.addresses = {}

    def add_address(self, address, port_id):
        """
        Adds the given address to the forwarding table at the given port, or
        updates the existing entry with the new port and a new timeout
        @param address : the address to add
        @param port : the port to add
        """
        self.addresses[address] = (port_id, datetime.datetime.now())

    def get_address_port(self, address):
        """
        Returns the port number for the given address, if not timed out
        @param address : the address to find the port
        @return int : the port number for the address, or False if not found
        """
        if address in self.addresses:
            time_passed_since_address_added = datetime.datetime.now() - self.addresses[address][1]
            if time_passed_since_address_added.total_seconds() >= 5:
                del self.addresses[address]
                return -1
            else:
                return self.addresses[address][0]
