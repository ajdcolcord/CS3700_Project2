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
    def __init__(self, bridgeID):
        """
        creates a new Bridge
        @param bridgeID : unique bridge id, set
        @param LAN_list : default to empty list, else, will hold the LANs
        """
        self.id = bridgeID
        self.rootPort_ID = None
        #self.cost = 0
        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, self.id, 0)
        self.ports = []
        print "Bridge " + self.id + " starting up\n"

    def create_ports_for_lans(self, LAN_list):
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
            print str(lan)
            if lan not in unique_lan_list:
                unique_lan_list.append(lan)

        print "UNIQUE LAN LIST: " + str(unique_lan_list)
        for lan in unique_lan_list:

            print "LAN = " + str(lan)
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            s.connect(self._pad(lan))
            port = Port(iterator, s)
            self.ports.append(port)
            print "CREATED LAN: " + str(lan) + " on port " + str(port.port_id)
            iterator += 1

        self.start_receiving()

    def start_receiving(self):
        """
        This function starts by broadcasting a BPDU, then runs the main loop
        for a Bridge that receives and sends messages and BPDUs to specific
        ports, and takes care of broadcasting BPDUs and messages to all ports
        """
        print "Number of Ports on this Bridge: " + str(len(self.ports))

        self._broadcast_BPDU()

        while True:
            ready, ignore, ignore2 = select.select([p.socket for p in self.ports], [], [], 0.1)
            for port in self.ports:
                if not port.BPDU_list:
                    port.designated = True
                    # recalculate root port from all of port's lists

                self._enable_or_disable(port)

                if ready:
                    print "RECEIVING FROM SOCKET ON PORT: " + str(port.port_id)
                    message = port.socket.recv(RECEIVE_SIZE)
                    message_json = json.loads(message)

                    if message_json['type'] == 'bpdu':
                        bpdu_in = BPDU(message_json['source'], message_json['dest'], message_json['message']['id'], message_json['message']['root'], message_json['message']['cost'])
                        self._port_decisions(bpdu_in, port)




                    '''
                    # TODO: THIS IS SENDING MESSAGES TO ALL PORTS FOR NOW
                    if message_json['type'] == 'data':
                    #    print "PARSED MESSAGE " + str(message_json['message']['id'])
                        for p in self.ports:
                            if p.port_id != port.port_id:
                                p.socket.send(message)

                    '''











    def _broadcast_BPDU(self):
        """
        Broadcasts a new BPDU from this bridge to all sockets
        """
        for port in self.ports:
            port.socket.send(self.bridge_BPDU.create_json_BPDU())


    def _port_decisions(self, bpdu_in, port_in):
        # if this bridge is the ROOT
        if not self.rootPort_ID:
            if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):

                # set bridge's bpdu to incoming bpdu (with cost updated)
                self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost + 1)
                self._print_new_root()

                # set bridge's root port to this port
                self.rootPort_ID = port_in.port_id
                self._print_root_port(self.rootPort_ID)

                # broadcast new information about the bridge
                self._broadcast_BPDU()
        else:
            if port_in.BPDU_list[0].is_incoming_BPDU_better(bpdu_in):
                if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                    self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost + 1)
                    self.rootPort_ID = port_in.port_id
                    self._print_root_port(port_in)

                else:
                    port_in.designated = True
            else:
                port_in.designated = False

        self._enable_or_disable(port_in)

    def _enable_or_disable(self, port):
        if port.designated or self.rootPort_ID == port.port_id:
            port.enabled = True
        else:
            port.enabled = False




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

    def _print_root_port(self, port_id):
        print "Root port: " + str(self.id) + "/" + str(port_id)
