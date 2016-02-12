#!/usr/bin/python -u

import sys
import socket
import select
from BPDU import BPDU, create_BPDU_from_json
from DataMessage import DataMessage, create_DataMessage_from_json
from ForwardingTable import ForwardingTable
from Port import Port
import time
import json

RECEIVE_SIZE = 1500


# check through all top BPDUs of all ports...
# for those that are the same, close the highest cost ports

class Bridge:
    """
    This is the class for a Bridge, which contains all the information
    for a network bridge
    """
    def __init__(self, bridgeID, LAN_list):
        """
        creates a new Bridge
        @param bridgeID : unique bridge id, set
        @param LAN_list : default to empty list, else, will hold the LANs
        """
        self.id = bridgeID
        self.rootPort_ID = None
        self.cost = 1
        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, self.id, self.cost)
        self.ports = []

        self._create_ports_for_lans(LAN_list)
        print "Bridge " + self.id + " starting up\n"
        self._start_receiving()

    def _create_ports_for_lans(self, LAN_list):
        """
        Creates a new socket with a respective port for each
        LAN in the LAN_list
        @LAN_list : List of LANs to create sockets for
        """
        iterator = 0
        print "THERE ARE: " + str(len(LAN_list)) + " INPUTTED LANS"
        print "LEN_LAN_LIST_RANGE = ", str(range(len(LAN_list)))
        print "LAN LIST = ", LAN_list

        unique_lan_list = []
        for lan in LAN_list:
            if lan not in unique_lan_list:
                unique_lan_list.append(lan)

        print "UNIQUE LAN LIST: " + str(unique_lan_list)
        for lan in unique_lan_list:

            print "LAN = " + str(lan)
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            port = Port(iterator, s)
            s.connect(self._pad(lan))
            self.ports.append(port)
            print "CREATED LAN: " + str(lan) + " on port " + str(port.port_id)
            iterator += 1



    def _start_receiving(self):
        """
        This function starts by broadcasting a BPDU, then runs the main loop
        for a Bridge that receives and sends messages and BPDUs to specific
        ports, and takes care of broadcasting BPDUs and messages to all ports
        """
        while True:
            ready, ignr, ignr2 = select.select([p.socket for p in self.ports], [], [], 0.5)
            for port in self.ports:
                ready, ignr, ignr2 = select.select([port.socket], [], [], 0.1)

                if ready:
                    message = ready[0].recv(RECEIVE_SIZE)
                    message_json = json.loads(message)

                    # TODO: THIS IS SENDING MESSAGES TO ALL PORTS FOR NOW
                    if message_json['type'] == 'data':
                        for port in self.ports:
                            port.socket.send(message)





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



    def _print_received_message(self, data_in_id, port_port_id, data_in_source, data_in_dest):
        print "Received message " + str(data_in_id) + "on port " + str(port_port_id) + \
            " from " + str(data_in_source) + " to " + str(data_in_dest)

    def _print_forwarding_message(self, data_in_id, port_port_id):
        print "Forwarding message " + str(data_in_id) + " to port " + str(port_port_id)

    def _print_boradcasting_message(self, data_in_id):
        print "Broadcasting message " + str(data_in_id) + " to all ports"

    def _print_not_forwarding_message(self, data_in_id):
        print "Not forwarding message " + str(data_in_id)

    def _print_disabled_port(self, port_in):
        print "Disabled port: " + str(self.id) + "/" + str(port_in)

    def _print_new_root(self):
        print "New root: " + str(self.id) + "/" + str(self.bridge_BPDU.root)
