#!/usr/bin/python -u

import sys
import socket
import select
from Packet import Packet
from BPDU import BPDU, create_BPDU_from_json
from DataMessage import DataMessage, create_DataMessage_from_json
from ForwardingTable import ForwardingTable
from Port import Port
import time
import random

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
        self.lans = []
        self.ports = []
        self.sockets = []
        self.rootID = self.id
        self.rootPort_ID = None
        self.cost = 1
        self.forwarding_table = ForwardingTable()

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
        for x in range(len(LAN_list)):
            if LAN_list[x] not in self.lans:
                # print "CREATING LAN: ", x
                s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                port = Port(iterator, s)
                s.connect(self._pad(LAN_list[x]))
                self.ports.append(port)
                self.sockets.append(s)
                iterator += 1
                self.lans.append(LAN_list[x])

    def _start_receiving(self):
        """
        This function starts by broadcasting a BPDU, then runs the main loop
        for a Bridge that receives and sends messages and BPDUs to specific
        ports, and takes care of broadcasting BPDUs and messages to all ports
        """
        start_time = time.time()

        self._broadcast_BPDU()

        BPDU_buffer = []

        # Main loop
        while True:
            for port in self.ports:
                ready, ignr, ignr2 = select.select([port.socket], [], [], 0.1)
                if ready:
                    message = ready[0].recv(RECEIVE_SIZE)
                    # attempt to create BPDU object from incoming message
                    bpdu_in = create_BPDU_from_json(message)
                    if bpdu_in:
                        port.add_BPDU(bpdu_in)
                        self._assign_new_root(bpdu_in, port.port_id)

                        #######
                        self._broadcast_BPDU()
                        #######

                        #if self.id != self.rootID:

                            ##########
                            #bpdu_in.cost += self.cost
                            #updated_bpdu = bpdu_in.create_json_BPDU()
                            #self._broadcast_message(updated_bpdu, port.port_id)
                            #############
                            #self._broadcast_message(message, port.port_id)
                            # BPDU_buffer.append(bpdu_in)

                    elif not bpdu_in:
                        data_in = create_DataMessage_from_json(message)
                        if data_in:
                            if port.enabled:
                                self._print_received_message(data_in.id, port.port_id, data_in.source, data_in.dest)

                                self.forwarding_table.add_address(data_in.source, port.port_id)

                                if data_in.dest in self.forwarding_table.addresses:
                                    self._print_forwarding_message(data_in.id, port.port_id)
                                    self._send_to_address(message, data_in.dest)
                                else:
                                    self._print_boradcasting_message(data_in.id)
                                    self._broadcast_message(message, port.port_id)
                            else:
                                self._print_not_forwarding_message(data_in.id)

                    for bpdu in port.BPDU_list:
                        #if bpdu.cost < self.cost or bpdu.source < self.id:
                        #    port.designated = False

                        #########
                        if bpdu.cost > self.cost and bpdu.source < self.id and bpdu.root == self.rootID:
                            port.designated = True
                        else:
                            port.designated = False
                        #########

                    if not port.BPDU_list or port.port_id == self.rootID or port.designated:
                        port.enabled = True
                    else:
                        port.enabled = False

            # is it time to send a new BPDU?
            # compare start time to current time, if > 500ms, send BPDU
            if int(round((time.time() - start_time) * 1000)) > 500:
                #if self.id == self.rootID:
                self._broadcast_BPDU()
                start_time = time.time()



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

    def _assign_new_root(self, bpdu_in, port_in):
        """
        Determines if the incoming BPDU contains a better root information
        than the current root than the current bridge root information
        @param BPDU_in : the BPDU to be checked if better
        @param port_in : the port that the bpdu_in was received
        """
        if self.id > bpdu_in.source:
            self.ports[port_in].enabled = False
            self._print_disabled_port(port_in)

        # if self.id < bpdu_in.source:
        #    self.ports[port_in].enabled = True

        oldRootPort = self.rootPort_ID
        if self.rootPort_ID:
            if self.ports[self.rootPort_ID].BPDU_list[0].is_incoming_BPDU_better(bpdu_in):
                self.rootID = bpdu_in.root
                self.rootPort_ID = port_in
                #self.cost += bpdu_in.cost
                self.cost = bpdu_in.cost + 1
                print "New root: " + str(self.id) + "/" + str(self.rootID)
                print "Root port: " + str(self.id) + "/" + str(self.rootPort_ID)
                self.ports[self.rootPort_ID].enabled = True
                # self.ports[oldRootPort].enabled = False
                #if self.id > bpdu_in.source:
                self.ports[port_in].enabled = False
                self._print_disabled_port(port_in)
                self.forwarding_table = ForwardingTable()


        elif self.rootID > bpdu_in.root:
                self.rootID = bpdu_in.root
                self.rootPort_ID = port_in
                # self.cost += bpdu_in.cost
                self.cost = bpdu_in.cost + 1
                print "New root: " + str(self.id) + "/" + str(self.rootID)
                print "Root port: " + str(self.id) + "/" + str(self.rootPort_ID)
                self.ports[self.rootPort_ID].enabled = True
                if self.id > bpdu_in.source:
                    self.ports[port_in].enabled = False
                    self._print_disabled_port(port_in)
                self.forwarding_table = ForwardingTable()

        if port_in == self.rootPort_ID:
            self.ports[port_in].enabled = True

    def _broadcast_BPDU(self):
        """
        Broadcasts a new BPDU from this bridge to all sockets. This
        will be done if this Bridge is the root
        """
        for port in self.ports:
            BPDU_unique_id = hex(random.randrange(0, 65534))
            newBPDU = BPDU(self.id, 'ffff', BPDU_unique_id, self.rootID, self.cost)
            port.socket.send(newBPDU.create_json_BPDU())

    def _broadcast_message(self, message, port_in):
        """
        Broadcasts the given message to all socket connections, except the
        inputted port
        @param message : string
        """
        for port in self.ports:
            if port != port_in:
                if port.enabled:
                    port.socket.send(message)

    def _send_to_address(self, message, address):
        """
        Sends the message inputted to the input address directly,
        using the forwarding table entry
        @param message : message to Sends
        @param address : address to send to
        """
        port_id = self.forwarding_table.get_address_port(address)
        if self.ports[port_id].enabled:
            self.ports[port_id].socket.send(message)

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
