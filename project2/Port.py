#!/usr/bin/python -u
from BPDU import BPDU
import socket
import time


class Port:
    def __init__(self, port_id, socket=None, enabled=True, BPDU_list=[]):
        self.port_id = port_id
        self.enabled = enabled
        self.BPDU_list = BPDU_list
        self.socket = socket

    def add_BPDU(self, BPDU):
        iterator = 0
        bpdu_added = False
        BPDU.time = time.time()
        if not self.BPDU_list:
            self.BPDU_list.insert(0, BPDU)
            bpdu_added = True
        for bpdu in self.BPDU_list:

            # If the bpdu has timed out, simply remove it
            if int(round((time.time() - bpdu.time) * 1000)) > 750:
                self.BPDU_list.remove(bpdu)

            if bpdu.is_incoming_BPDU_better(BPDU) and not bpdu_added:
                self.BPDU_list.insert(iterator, BPDU)
                bpdu_added = True
                print "ADDED BPDU TO PORT: ", self.port_id

            iterator += 1

        if not bpdu_added:
            self.BPDU_list.append(BPDU)
