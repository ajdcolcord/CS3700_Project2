#!/usr/bin/python -u

import sys
import socket
import select
from BPDU import BPDU, create_BPDU_from_json
from DataMessage import DataMessage, create_DataMessage_from_json
from ForwardingTable import ForwardingTable
from Port import Port
import time

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
        self.rootPort_ID = None
        self.cost = 1
        self.forwarding_table = ForwardingTable()
        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, self.id, self.cost)

        self._create_ports_for_lans(LAN_list)
        print "Bridge " + self.id + " starting up\n"
        self._broadcast_BPDU()
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

        while True:
            # is it time to send a new BPDU?
            if int(round((time.time() - start_time) * 1000)) > 500:
                self._broadcast_BPDU()
                start_time = time.time()

            # TODO: port.remove_all_timedout_BPDUs()
            for port in self.ports:
                port.remove_all_timedout_BPDUs()
            # TODO: update_bridge
            br_updated = self._update_bridge()
            if br_updated:
                start_time = time.time()
            # TODO: for port in self.ports: update_port(self.bridge_BPDU)
            for port in self.ports:
                self.update_port(port)
                start_time = time.time()


            ready, ignr, ignr2 = select.select([p.socket for p in self.ports], [], [], 0.5)
            for port in self.ports:
                if ready:
                    message = ready[0].recv(RECEIVE_SIZE)
                    bpdu_in = create_BPDU_from_json(message)
                    if bpdu_in:
                        bpdu_in.timeout = time.time()
                        print "BPDU"
                        port.add_BPDU(bpdu_in)
                        # TODO: WHAT IF PORT's TOP BPDU EXPIRES?
                        changed = self._update_port(port)

                        if changed:
                            print "PORT CHANGED"
                            b_changed = self._update_bridge()
                            if b_changed:
                                print "BRIDGE CHANGED"
                                for thisPort in self.ports:
                                    self._update_port(thisPort)
                                self._broadcast_BPDU()
                                start_time = time.time()

                    elif not bpdu_in:
                        print "DATA MESSAGE"
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



    #before this, incoming BPDU was added to the port's list
    def _update_port(self, port):
        print "UPDATING PORT"
        # determine if this port shoudl be enabled or disabled
        is_root = port.port_id == self.rootPort_ID

         # if this bridge's BPDU is better than the best bpdu seen so far on this port
        is_designated = port.BPDU_list[0].is_incoming_BPDU_better(self.bridge_BPDU)

        is_enabled = is_root or is_designated
        result = is_enabled != port.enabled

        port.enabled = is_enabled

        # TODO: print stuff (disabled, designated, root)
        return result

    def _update_bridge(self):
        print "UPDATING BRIDGE"
        # determine if this bridge should be updated
        # go through the tops of all ports and check if any are better than this bridge's BPDU
        # return True if updated, False if not
        result = False
        for port in self.ports:
            if port.BPDU_list:
                if self.bridge_BPDU.is_incoming_BPDU_better(port.BPDU_list[0]):
                    self.bridge_BPDU = port.BPDU_list[0]
                    self.rootPort_ID = port.port_id
                    self.cost = port.BPDU_list[0].cost + 1
                    #self.forwarding_table = ForwardingTable()
                    self._print_new_root()
                    result = True
        if result:
            self._broadcast_BPDU()
        return result

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

    def _broadcast_BPDU(self):
        """
        Broadcasts a new BPDU from this bridge to all sockets. This
        will be done if this Bridge is the root
        """
        for port in self.ports:
            newBPDU = BPDU(self.id, 'ffff', 1, self.bridge_BPDU.root, self.cost)
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

    def _print_new_root(self):
        print "New root: " + str(self.id) + "/" + str(self.bridge_BPDU.root)
