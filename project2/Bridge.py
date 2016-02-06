#!/usr/bin/python -u

import sys
import socket
import select
import json
from Packet import Packet

RECEIVE_SIZE = 1500


class Bridge:
    def __init__(self, bridgeID, LAN=[]):
        self.id = bridgeID
        self.LAN_list = LAN
        self.sockets = []
        self._create_sockets_for_lans()
        self._start_receiving()

    def _create_sockets_for_lans(self):
        for x in range(len(self.LAN_list)):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            s.connect(self._pad(self.LAN_list[x]))
            self.sockets.append(s)

    def _start_receiving(self):
        # Main loop
        while True:
            # Calls select with all the sockets; change the timeout value (1)
            ready, ignore, ignore2 = select.select(self.sockets, [], [], 1)

            # Reads from each fo the ready sockets
            for x in ready:
                message = x.recv(RECEIVE_SIZE)

                # create new packet object from the incoming message
                packet = Packet(message)

    def _pad(self, name):
        # pads the name with null bytes at the end
        result = '\0' + name
        while len(result) < 108:
                result += '\0'
        return result
