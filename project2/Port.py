#!/usr/bin/python -u
from BPDU import BPDU


class Port:
    def __init__(self, port_id, enabled=True, socket=None, BPDU_list=[]):
        self.port_id = port_id
        self.enabled = enabled
        self.BPDU_list = BPDU_list
        self._open_socket()

    def _open_socket():
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.socket = sock

    def add_BPDU(self, BPDU):
        iterator = 0
        for bpdu in self.BPDU_list:
            if bpdu.is_incoming_BPDU_better(BPDU):
                self.BPDU_list.insert(iterator, BPDU)
            iterator += 1
