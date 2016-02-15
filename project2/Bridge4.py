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
        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, self.id, 0)
        self.ports = []
        self.sockets = {}
        self.forwarding_table = ForwardingTable()

    def create_ports_for_lans(self, LAN_list):
        """
        Creates a new socket with a respective port for each
        LAN in the LAN_list
        @LAN_list : List of LANs to create sockets for
        """
        print "Bridge " + self.id + " starting up\n"
        iterator = 0
        unique_lan_list = []

        for lan in LAN_list:
            print str(lan)
            if lan not in unique_lan_list:
                unique_lan_list.append(lan)

        for lan in unique_lan_list:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            s.connect(self._pad(lan))
            port = Port(iterator, s)
            self.ports.append(port)
            self.sockets[s] = port.port_id
            iterator += 1

        self.start_receiving()

    def start_receiving(self):
        """
        This function starts by broadcasting a BPDU, then runs the main loop
        for a Bridge that receives and sends messages and BPDUs to specific
        ports, and takes care of broadcasting BPDUs and messages to all ports
        """
        print "Number of Ports on this Bridge: " + str(len(self.ports))

        start_time = time.time()
        self._broadcast_BPDU()

        while True:
            # self._print_bridge_info()

            # is it time to send a new BPDU?
            if int(round((time.time() - start_time) * 1000)) > 500:
                self._broadcast_BPDU()
                start_time = time.time()

            ready, ignore, ignore2 = select.select([port.socket for port in self.ports], [], [], 0.1)

            for x in ready:

                port = self.ports[self.sockets[x]]

                if not port.BPDU_list:
                    # if port not designated, print out designated
                    if not port.designated:
                        self._print_designated_port(port.port_id)
                    port.designated = True

                    # recalculate root port from all of port's lists...

                self._enable_or_disable(port)

                message = port.socket.recv(RECEIVE_SIZE)
                message_json = json.loads(message)

                if message_json['type'] == 'bpdu':
                    #print "RECEIVING BPDU FROM SOCKET ON PORT: " + str(port.port_id) + " FROM " + message_json['source']

                    bpdu_in = BPDU(message_json['source'], message_json['dest'], message_json['message']['id'], message_json['message']['root'], message_json['message']['cost'])# + 1)

                    self._received_bpdu_logic(bpdu_in, port)
                    '''
                    original_root_port = self.rootPort_ID
                    saved_bpdu = None
                    if self.rootPort_ID:
                        saved_bpdu = self.ports[original_root_port].BPDU_list[0]

                    self._port_decisions(bpdu_in, port)

                    if original_root_port:
                        if self.rootPort_ID != original_root_port:
                            self.forwarding_table = ForwardingTable() # clear forwarding table
                            if self.ports[original_root_port].BPDU_list:
                                if saved_bpdu:
                                    if saved_bpdu.is_incoming_BPDU_better(self.bridge_BPDU):
                                        self.ports[original_root_port].designated = True
                                        self._enable_or_disable(self.ports[original_root_port])
                            else:
                                self.ports[original_root_port].designated = True
                                self._enable_or_disable(self.ports[original_root_port])
                    '''

                elif message_json['type'] == 'data':
                    #print "DATA MESSAGE FROM: " + str(message_json['source'])

                    data_in = create_DataMessage_from_json(message)

                    if data_in:
                        #self._enable_or_disable(port)

                        if port.enabled:
                            self._print_received_message(data_in.id, port.port_id, data_in.source, data_in.dest)
                            self.forwarding_table.add_address(data_in.source, port.port_id)

                            sending_port_id = self.forwarding_table.get_address_port(data_in.dest)

                            if sending_port_id >= 0 and self.ports[sending_port_id].enabled:
                                if sending_port_id == port.port_id:
                                    self._print_not_forwarding_message(data_in.id)
                                else:
                                    self._print_forwarding_message(data_in.id, port.port_id)
                                    self.ports[sending_port_id].socket.send(message)

                            else:
                                self._broadcast_message(message, port)

                            '''

                            print "PORT " + str(port.port_id) + " ENABLED FOR MESSAGE: " + str(data_in.id) + " From " + str(data_in.source)

                            self._print_received_message(data_in.id, port.port_id, data_in.source, data_in.dest)

                            self.forwarding_table.add_address(data_in.source, port.port_id)

                            sending_port_id = self.forwarding_table.get_address_port(data_in.dest)

                            # if in the forwarding table, and not expired, send on that port
                            if sending_port_id >= 0 and self.ports[sending_port_id].BPDU_list:
                                print "SENDING_PORT_ID Exists (" + str(sending_port_id) + ") - and Not Expired"
                                if self.ports[sending_port_id].remove_timedout_BPDU(self.ports[sending_port_id].BPDU_list[0]):
                                    print "BPDU WAS TIMED OUT ON PORT-" + str(sending_port_id) + " SHOULD BROADCAST"
                                    #self.forwarding_table = ForwardingTable()
                                    #self._print_boradcasting_message(data_in.id)
                                    self._broadcast_message(message, port.port_id, data_in.id)
                                else:
                                    print "BPDU NOT TIMED OUT ON PORT-" + str(sending_port_id) + " FORWARDING ON PORT " + str(sending_port_id)

                                    if port.port_id != sending_port_id:
                                        self._print_forwarding_message(data_in.id, port.port_id)
                                        self._send_to_address(message, sending_port_id)
                            else:
                                print "SENDING_PORT EXPIRED OR NOT IN FORWARDING TABLE FOR MESSAGE- " + str(data_in.id)
                                #self._print_boradcasting_message(data_in.id)
                                self._broadcast_message(message, port.port_id, data_in.id)
                            '''
                        else:
                            self._print_not_forwarding_message(data_in.id)

    def _received_bpdu_logic(self, bpdu, port):
        original_root_port = self.rootPort_ID
        saved_bpdu = None
        if original_root_port:
            saved_bpdu = self.ports[original_root_port].BPDU_list[0]

        self._port_decisions(bpdu, port)

        if original_root_port:
            if self.rootPort_ID != original_root_port:
                self.forwarding_table = ForwardingTable() # clear forwarding table
                if self.ports[original_root_port].BPDU_list:
                    if saved_bpdu:
                        if saved_bpdu.is_incoming_BPDU_better(self.bridge_BPDU):
                            self.ports[original_root_port].designated = True
                            self._enable_or_disable(self.ports[original_root_port])
                else:
                    self.ports[original_root_port].designated = True
                    self._enable_or_disable(self.ports[original_root_port])


    def _port_decisions(self, bpdu_in, port_in):
        # if this bridge is currently the ROOT...
        if self.rootPort_ID is None:

            # if incoming BPDU has a better bridge than this one
            if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):

                changed_root = self.bridge_BPDU.root != bpdu_in.root
                changed_root_id = self.rootPort_ID != port_in.port_id

                # set bridge's bpdu to incoming bpdu (with cost updated)
                self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost + 1)

                if changed_root:
                    self._print_new_root()

                # set bridge's root port to this port
                self.rootPort_ID = port_in.port_id
                port_in.designated = False

                if changed_root_id:
                    self._print_root_port(self.rootPort_ID)

                self.forwarding_table = ForwardingTable()

                port_in.add_BPDU(bpdu_in)
                self._broadcast_BPDU()
            else:
                # This bridge is better than the bridge on the incoming BPDU, stays the root
                port_in.add_BPDU(bpdu_in)

        # if this bridge is currently NOT the root...
        else:
            # if the incoming BPDU is better than the current port's bpdu (seeing a better bridge)
            if port_in.BPDU_list[0].is_incoming_BPDU_better(bpdu_in):

                # if the incoming BPDU is also better than the bridge's information (better bridge seen)
                if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):

                    # if the incoming bpdu's source is not the same as this bridge's current root port's bpdu's source
                    if self.ports[self.rootPort_ID].BPDU_list[0].source != bpdu_in.source:

                        changed_root = self.bridge_BPDU.root != bpdu_in.root
                        changed_root_id = self.rootPort_ID != port_in.port_id

                        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost + 1)

                        if changed_root:
                            self._print_new_root()

                        self.rootPort_ID = port_in.port_id
                        port_in.designated = False

                        if changed_root_id:
                            self._print_root_port(self.rootPort_ID)

                        port_in.add_BPDU(bpdu_in)

                        if changed_root or changed_root_id:
                            self.forwarding_table = ForwardingTable()

                        # broadcast new information about the bridge
                        self._broadcast_BPDU()
                    else:
                        if port_in.designated:
                            self.forwarding_table = ForwardingTable()

                        port_in.designated = False
                        port_in.add_BPDU(bpdu_in)

                else:
                    if not port_in.designated:
                        self._print_designated_port(port_in.port_id)

                    port_in.designated = False
                    port_in.add_BPDU(bpdu_in)

            else:
                if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                    if port_in.designated:
                        self.forwarding_table = ForwardingTable()

                    port_in.designated = False

                port_in.add_BPDU(bpdu_in)

        self._enable_or_disable(port_in)

    def _enable_or_disable(self, port):
        previous_status = port.enabled
        if port.designated or self.rootPort_ID == port.port_id:
            port.enabled = True
            if previous_status != port.enabled:
                self.forwarding_table = ForwardingTable()
                # self._print_bridge_info()
        else:
            port.enabled = False
            if previous_status != port.enabled:
                self._print_disabled_port(port.port_id)
                self.forwarding_table = ForwardingTable()
                # self._print_bridge_info()

    def _broadcast_BPDU(self):
        """
        Broadcasts a new BPDU from this bridge to all sockets
        """
        for port in self.ports:
            port.socket.send(self.bridge_BPDU.create_json_BPDU())

    def _broadcast_message(self, message, port_in):
        """
        Broadcasts the given message to all socket connections, except the
        inputted port
        @param message : string
        """
        for port in self.ports:
            if port.port_id != port_in.port_id:
                self._enable_or_disable(port)
                if port.enabled:
                    port.socket.send(message)

    def _send_to_address(self, message, dest_port_id):
        """
        Sends the message inputted to the input address directly,
        using the forwarding table entry
        @param message : message to Sends
        @param address : address to send to
        """
        #port_id = self.forwarding_table.get_address_port(address)
        #if self.ports[port_id].enabled:
        self.ports[dest_port_id].socket.send(message)

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

    def _print_disabled_port(self, port_id):
        print "Disabled port: " + str(self.id) + "/" + str(port_id)

    def _print_new_root(self):
        print "New root: " + str(self.id) + "/" + str(self.bridge_BPDU.root)

    def _print_root_port(self, port_id):
        print "Root port: " + str(self.id) + "/" + str(port_id)

    def _print_designated_port(self, port_id):
        print "Designated port: " + str(self.id) + "/" + str(port_id)

    def _print_bridge_info(self):
        port_status_list = ""
        for port in self.ports:
            port_status_list += "\tPort-" + str(port.port_id) + "-Enabled=" + str(port.enabled) + "-Designated=" + str(port.designated)
        print "BRIDGE - " + str(self.id) + " ROOT= " + str(self.bridge_BPDU.root) + " COST= " + str(self.bridge_BPDU.cost) + " ROOT PORT= " + str(self.rootPort_ID) + " PORTS:[" + str(port_status_list) + "]\n"
