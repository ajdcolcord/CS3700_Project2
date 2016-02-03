

class ForwardingTable:

    def __init__(self):
        self.address_ports = {}

    def add_address_to_port(self, port, address):
        self.address_ports[address] = port