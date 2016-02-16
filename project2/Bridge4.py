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
            self._print_bridge_info()
            # is it time to send a new BPDU?
            if int(round((time.time() - start_time) * 1000)) > 500:
                print "BROADCASTING BPDU"
                self._broadcast_BPDU()
                start_time = time.time()

            ready, ignore, ignore2 = select.select([port.socket for port in self.ports], [], [], 0.1)
            for x in ready:
                port = self.ports[self.sockets[x]]

                if not port.BPDU_list:
                    # if port not designated, print out designated
                    if not port.designated:
                        self._print_designated_port(port.port_id)
                        self.forwarding_table = ForwardingTable()
                    port.designated = True

                    # recalculate root port from all of port's lists...

                self._enable_or_disable(port)

                message = port.socket.recv(RECEIVE_SIZE)
                message_json = json.loads(message)

                if message_json['type'] == 'bpdu':
                    bpdu_in = BPDU(message_json['source'], message_json['dest'], message_json['message']['id'], message_json['message']['root'], message_json['message']['cost'])# + 1)
                    self._received_bpdu_logic(bpdu_in, port)

                elif message_json['type'] == 'data':
                    data_in = create_DataMessage_from_json(message)
                    self._received_data_logic(data_in, port, message)

    def _received_bpdu_logic(self, bpdu, port):
        """
        This function handles all of the logic for when a BPDU message is received. It also takes care
        of if the root port changed, if that port should now be designated or not
        :param bpdu: the incoming BPDU
        :param port: the port that the BPDU came in on
        :return: Void
        """
        print "RECEIVED BPDU FROM " + str(bpdu.source) + " ON PORT " + str(port.port_id) + " COST = " + str(bpdu.cost) + " ROOT = " + str(bpdu.root)
        self._print_bridge_info()

        '''
        original_root_port = self.rootPort_ID
        saved_bpdu = None
        if original_root_port:
            saved_bpdu = self.ports[original_root_port].BPDU_list[0]
        '''
        self._port_decisions_2(bpdu, port)
        '''
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
        #self._enable_or_disable(port)

    def _received_data_logic(self, data_in, port, message):
        """
        This function holds the functionality needed for when a data message is received. After it is
        Received, if the port is enabled, the message is either forwarded on a different port, if
        the address is in the forwarding table, broadcasted if the address isn't (or has expired),
        or not broadcasted (if the forwarding table says that the address is on the incoming port,
        or if the incoming port is disabled)
        :param data_in: the DataMessage object to send
        :param port: the port that the message came in on
        :param message: the raw json message to send (so no re-encoding is needed)
        :return: Void
        """
        if data_in:
            self._enable_or_disable(port)

            if port.enabled:
                self._print_received_message(data_in.id, port.port_id, data_in.source, data_in.dest)
                self.forwarding_table.add_address(data_in.source, port.port_id)

                sending_port_id = self.forwarding_table.get_address_port(data_in.dest)

                if sending_port_id >= 0 and self.ports[sending_port_id].enabled:
                    if self.ports[sending_port_id].BPDU_list and self.ports[sending_port_id].remove_timedout_BPDU(self.ports[sending_port_id].BPDU_list[0]):
                        print "BPDU WAS TIMED OUT ON PORT-" + str(sending_port_id) + " SHOULD BROADCAST"
                        self.forwarding_table = ForwardingTable()
                        self._print_boradcasting_message(data_in.id)
                        self._broadcast_message(message, port)
                        return
                    else:
                        if sending_port_id == port.port_id:
                            print "NOT FORWARDING MESSAGE " + str(data_in.id) + "-  NOT IN FORWARDING TABLE - ENABLED = " + str(self.ports[sending_port_id].enabled)
                            self._print_not_forwarding_message(data_in.id)
                            #self._print_boradcasting_message(data_in.id)
                            #self._broadcast_message(message, port)
                            return
                        else:
                            print "FORWARDING MESSAGE " + str(data_in.id) + "- IN FORWARDING TABLE and ENABLED = " + str(self.ports[sending_port_id].enabled)
                            self._print_forwarding_message(data_in.id, port.port_id)
                            self.ports[sending_port_id].socket.send(message)
                            return
                else:
                    self._print_boradcasting_message(data_in.id)
                    self._broadcast_message(message, port)
                    return
            else:
                print "NOT FORWARDING MESSAGE " + str(data_in.id) + " BECAUSE INCOMING PORT NOT ENABLED- " + str(port.port_id)
                self._print_not_forwarding_message(data_in.id)
                return

    def _port_decisions_2(self, bpdu_in, port_in):
        """
        This function holds all of the decisions for a port when a BPDU comes in.
        - If the bridge currently think's it's the root, it checks if the BPDU holds a better path than this
          bridge to a better root, if so, this bridge takes on the new path and information.
        - If this bridge is not the root, it checks if the incoming BPDU is better than any seen on the incoming port,
          if so, it then checks if it is also better than the bridge. If so, it takes on the new path. If it isn't
          better than the bridge, but still better than the port, the port's designated status gets set to false.
        - If this bridge is not the root, and the BPDU is not better than what is on this port, then the port gets
          undesignated
        :param bpdu_in: the incoming BPDU
        :param port_in: the incoming port
        :return: Void
        """
        # if this bridge is currently the ROOT...
        if self.rootPort_ID is None:
            # if incoming BPDU has a better bridge than this one
            if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                self._change_root(port_in, bpdu_in)
            #else:
            # This bridge is better than the bridge on the incoming BPDU, stays the root
            #port_in.add_BPDU(bpdu_in)

        # if this bridge is currently NOT the root...
        else:
            # if the incoming BPDU is better than the current port's bpdu (seeing a better bridge)
            if port_in.BPDU_list[0].is_incoming_BPDU_better(bpdu_in):

                # if the incoming BPDU is also better than the bridge's information (better bridge seen)
                #if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                root_bpdu = self.ports[self.rootPort_ID].BPDU_list[0]
                if root_bpdu.is_incoming_BPDU_better(bpdu_in):

                    # if the incoming bpdu's source is not the same as this bridge's current root port's bpdu's source
                    #if self.ports[self.rootPort_ID].BPDU_list[0].source != bpdu_in.source:
                    self._change_root(port_in, bpdu_in)

        port_in.add_BPDU(bpdu_in)
        self._designate_port(port_in)
        self._enable_or_disable(port_in)

    def _designate_port(self, port):
        if port.BPDU_list[0].is_incoming_BPDU_better(self.bridge_BPDU):
            port.designated = True
            print "PORT BPDU = " + str(port.BPDU_list[0].create_json_BPDU()) + " --- BRIDGE BPDU = " + str(self.bridge_BPDU.create_json_BPDU()) + " TRUE"

        else:
            print "PORT BPDU = " + str(port.BPDU_list[0].create_json_BPDU()) + " --- BRIDGE BPDU = " + str(self.bridge_BPDU.create_json_BPDU()) + " FALSE"
            port.designated = False

    def _port_decisions(self, bpdu_in, port_in):
        """
        This function holds all of the decisions for a port when a BPDU comes in.
        - If the bridge currently think's it's the root, it checks if the BPDU holds a better path than this
          bridge to a better root, if so, this bridge takes on the new path and information.
        - If this bridge is not the root, it checks if the incoming BPDU is better than any seen on the incoming port,
          if so, it then checks if it is also better than the bridge. If so, it takes on the new path. If it isn't
          better than the bridge, but still better than the port, the port's designated status gets set to false.
        - If this bridge is not the root, and the BPDU is not better than what is on this port, then the port gets
          undesignated
        :param bpdu_in: the incoming BPDU
        :param port_in: the incoming port
        :return: Void
        """
        # if this bridge is currently the ROOT...
        if self.rootPort_ID is None:
            # if incoming BPDU has a better bridge than this one
            if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                self._change_root(port_in, bpdu_in)
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
                        self._change_root(port_in, bpdu_in)
                    else:
                        if port_in.designated:
                            self.forwarding_table = ForwardingTable()

                        port_in.designated = False
                        port_in.add_BPDU(bpdu_in)

                else:
                    if not port_in.designated:
                        self._print_designated_port(port_in.port_id)

                    self.forwarding_table = ForwardingTable()

                    port_in.designated = False
                    port_in.add_BPDU(bpdu_in)

            else:
                # TODO: TROUBLE SPOT HERE -------
                #bpdu_in.cost += 1

                if self.bridge_BPDU.is_incoming_BPDU_better(bpdu_in):
                    #if port_in.designated:

                    self.forwarding_table = ForwardingTable()

                    '''
                    ###NEW###

                    changed_root = self.bridge_BPDU.root != bpdu_in.root
                    changed_root_id = self.rootPort_ID != port_in.port_id

                    self.rootPort_ID = port_in.port_id
                    self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost)# + 1)

                    if changed_root_id:
                        self._print_root_port(self.rootPort_ID)
                    if changed_root:
                        self._print_new_root()

                    self._broadcast_BPDU()

                    #########

                    port_in.designated = False
                    else:
                    if bpdu_in.cost == self.bridge_BPDU.cost and self.id < bpdu_in.source:
                        port_in.designated = True
                    else:
                        port_in.designated = False
                    #else:
                    '''
                    port_in.designated = False

                port_in.add_BPDU(bpdu_in)

        self._enable_or_disable(port_in)

    def _change_root(self, port_in, bpdu_in):
        """
        This function updates the root information for the incoming BPDU on the port_in
        Since this is used a few times, this function was created to minimize redundancy
        :param port_in: the port the bpdu was received on
        :param bpdu_in: the bpdu that will update this bridge's root information
        :return: Void
        """
        changed_root = self.bridge_BPDU.root != bpdu_in.root
        changed_root_id = self.rootPort_ID != port_in.port_id

        self.bridge_BPDU = BPDU(self.id, 'ffff', 1, bpdu_in.root, bpdu_in.cost + 1)

        if changed_root:
            self._print_new_root()

        # set bridge's root port to this port
        self.rootPort_ID = port_in.port_id
        port_in.designated = False

        if changed_root_id:
            self._print_root_port(self.rootPort_ID)

        if changed_root or changed_root_id:
            self.forwarding_table = ForwardingTable()

        #port_in.add_BPDU(bpdu_in)
        self._broadcast_BPDU()

    def _enable_or_disable(self, port):
        """
        This function simply checks if the port is designated or root.
        If neither, it sets it to disabled. If either,it gets set to enabled.
        :param port: the port to check
        :return: Void
        """
        previous_status = port.enabled
        if port.designated or self.rootPort_ID == port.port_id:
            port.enabled = True
            if previous_status != port.enabled:
                self.forwarding_table = ForwardingTable()
        else:
            port.enabled = False
            if previous_status != port.enabled:
                self._print_disabled_port(port.port_id)
                self.forwarding_table = ForwardingTable()

    def _broadcast_BPDU(self):
        """
        Broadcasts a new BPDU from this bridge to all sockets on the bridge
        @return: Void
        """
        for port in self.ports:
            port.socket.send(self.bridge_BPDU.create_json_BPDU())

    def _broadcast_message(self, message, port_in):
        """
        Broadcasts the given message to all socket connections, except the
        given port
        @param message : string
        @return: Void
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
        @return Void
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
        """
        This function prints that a message was received on the port
        :param data_in_id: the ID of the message
        :param port_port_id: the port that the message came in on
        :param data_in_source: the source of the message
        :param data_in_dest: the destination of the message
        :return: Void
        """
        print "Received message " + str(data_in_id) + "on port " + str(port_port_id) + \
            " from " + str(data_in_source) + " to " + str(data_in_dest)

    def _print_forwarding_message(self, data_in_id, port_port_id):
        """
        This function prints that the message was forwarded to the given port
        :param data_in_id: the message ID
        :param port_port_id: the port that the message was forwarded on
        :return: Void
        """
        print "Forwarding message " + str(data_in_id) + " to port " + str(port_port_id)

    def _print_boradcasting_message(self, data_in_id):
        """
        This function prints that a message is being broadcasted on all ports (except the incoming port)
        :param data_in_id: the message ID
        :return: Void
        """
        print "Broadcasting message " + str(data_in_id) + " to all ports"

    def _print_not_forwarding_message(self, data_in_id):
        """
        This function prints that the message is not being forwarded
        :param data_in_id: the message ID
        :return: Void
        """
        print "Not forwarding message " + str(data_in_id)

    def _print_disabled_port(self, port_id):
        """
        This function prints that the given port was disabled
        :param port_id: the ID of the port being disabled
        :return: Void
        """
        print "Disabled port: " + str(self.id) + "/" + str(port_id)

    def _print_new_root(self):
        """
        This function prints that a new root was found for this bridge
        :return: Void
        """
        print "New root: " + str(self.id) + "/" + str(self.bridge_BPDU.root)

    def _print_root_port(self, port_id):
        """
        This function prints that this bridge has a new root port
        :param port_id: the new root port id
        :return: Void
        """
        print "Root port: " + str(self.id) + "/" + str(port_id)

    def _print_designated_port(self, port_id):
        """
        This function prints that this port is designated
        :param port_id: the port being designated
        :return: Void
        """
        print "Designated port: " + str(self.id) + "/" + str(port_id)

    def _print_bridge_info(self):
        """
        This function is used to print out all of the information on this bridge, including the status of it's ports
        :return: Void
        """
        port_status_list = ""
        for port in self.ports:
            port_status_list += "\tPort-" + str(port.port_id) + "-Enabled=" + str(port.enabled) + "-Designated=" + str(port.designated)
        print "BRIDGE - " + str(self.id) + " ROOT= " + str(self.bridge_BPDU.root) + " COST= " + str(self.bridge_BPDU.cost) + " ROOT PORT= " + str(self.rootPort_ID) + " PORTS:[" + str(port_status_list) + "]\n"
