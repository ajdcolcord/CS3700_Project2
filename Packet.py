import socket
import time


class Packet:
    def __init__(self, source, type, dest='ffff', message={}):
        self.source = source
        self.type = type
        self.dest = dest
        self.message = message


def broadcast_bpdu():

    host = ''

    for x in range(10000, 65536):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print "Host", host
        print "Port", x
        try:
            s.bind((host, x))
        except:
            print "Already in use"

        data = "Time" + repr(time.time()) + '\n'
        s.sendto(data, ('<broadcast>', x))

    time.sleep(1)
