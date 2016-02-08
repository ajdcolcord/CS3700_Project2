#!/usr/bin/python -u

import sys
import socket
import select

RECEIVE_SIZE = 1500


# check through all top BPDUs of all ports...
# for those that are the same, close the highest cost ports

class Bridge:
    """
    This is the class for a Bridge, which contains all the information
    for a network bridge
    """
    def __init__(self, bridgeID, LAN_list=[]):
        """
        creates a new Bridge
        @param bridgeID : unique bridge id, set
        @param LAN_list : default to empty list, else, will hold the LANs
        """
        self.id = bridgeID
        self.ports = {}
        self._create_ports_for_lans(LAN_list)

    def _create_ports_for_lans(self, LAN_list):
        """
        Creates a new socket with a respective port for each
        LAN in the LAN_list
        @LAN_list : List of LANs to create sockets for
        """
        port_id = 0
        lans = []
        for x in range(len(LAN_list)):
            if LAN_list[x] not in lans:
                lans.append(LAN_list[x])
                print "CREATING LAN: ", x
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                sock.connect(self._pad(LAN_list[x]))
                self.ports[port_id] = sock
                port_id += 1

    def _start_receiving(self):
        while True:
            ready, ignr, ignr2 = select.select(self.ports, [], [], 1)

            for x in ready:
                data = x.recv(RECEIVE_SIZE)
                print (data)

    def _pad(self, name):
        """
        Pads the name with null bytes at the end
        @param name : the name to pad
        @return String
        """
        result = '\0' + name
        while len(result) < 108:
            result += '\0'
        return result

