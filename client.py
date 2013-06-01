import sys
import time
import zmq

class Client(object):
    def __init__(self, server_addresses, timeout = 2.5):
        self.server_addresses = server_addresses
        self.timeout = timeout
        self.sequence = 0
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        for server_address in server_addresses:
            print "Client:", server_address
            self.socket.connect(server_address)
        self.poll = zmq.Poller()
        self.poll.register(self.socket, zmq.POLLIN)

    def destroy(self):
        self.socket.setsockopt(zmq.LINGER, 0)  # Terminate early
        self.socket.close()
        self.context.term()
        
    def send(self, msg):
        self.sequence += 1
        msg = ['', str(self.sequence)] + msg
        # Blast the request to all connected servers
        for server in xrange(len(self.server_addresses)):
            self.socket.send_multipart(msg)
        return self.sequence
            
    def recv(self, sequence):
        # wait (with timeout) for the first valid response that matches the sequence number
        endtime = time.time() + self.timeout
        while time.time() < endtime:
            msg = None
            socks = dict(self.poll.poll((endtime - time.time())))
            if socks.get(self.socket) == zmq.POLLIN:
                msg = self.socket.recv_multipart()
                assert len(msg) >= 5
                sequence = int(msg[1])
                if sequence == self.sequence and msg[4]:
                    break
        return msg

    def request(self, request):
        msg = ['REQ', request, '']

        # send it to all servers
        seq = self.send(msg)

        # wait (with timeout) for the first response that matches the sequence number
        reply = self.recv(seq)
        if reply:
            return reply[4]
        
    def push(self, key, value):
        msg = ['PUSH', key, value]

        # send it to all servers
        seq = self.send(msg)

        # wait (with timeout) for the first response that matches the sequence number
        return self.recv(seq)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice test client")
    parser.add_argument('--request',
                        help="request key")
    parser.add_argument('--push',
                        help="push key:value (use colon as separator)")
    parser.add_argument('servers', nargs='+',
                        help="server(s)")
    args = parser.parse_args()

    client = Client(args.servers)
    if args.request:
        print client.request(args.request)
    if args.push:
        pair = args.push.split(':')
        print client.push(pair[0], pair[1])
    client.destroy()
