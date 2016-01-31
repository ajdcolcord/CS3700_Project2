import socket
import traceback
import time

host = ''

port = 50000

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind((host, port))

while 1:
    data = repr(time.time()) + '\n'
    s.sendto(data, ('<broadcast>', port))
    time.sleep(1)
    '''
    try:
        message, address = s.recvfrom(8192)
        print "GOT DATA FROM : ", address
        s.sendto("I am here", address)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        traceback.print_exc()
    '''
