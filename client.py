import sys
import time
import zmq
import collections

class Client(object):
    def __init__(self, server_addresses, timeout = 2.5):
        self.protocol = 'names0.1'
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
        msg = ['', self.protocol, str(self.sequence)] + msg
        # Blast the request to all connected servers
        for server in xrange(len(self.server_addresses)):
            self.socket.send_multipart(msg)
        return self.sequence
            
    def recv(self, sequence, validfunc):
        # wait (with timeout) for responses that match the sequence number until validfunc returns valid dict
        union = collections.defaultdict(set)
        endtime = time.time() + self.timeout
        while time.time() < endtime:
            socks = dict(self.poll.poll((endtime - time.time())))
            if socks.get(self.socket) == zmq.POLLIN:
                msg = self.socket.recv_multipart()
                assert msg[1] == self.protocol
                sequence = int(msg[2])
                msg = msg[3:]
                if sequence == self.sequence:
                    while len(msg):
                        key = msg[0]
                        value = msg[1]
                        msg = msg[2:]
                        if value:
                            union[key].add(value)
                    resp = validfunc(union)
                    if resp:
                        return union, True
        return union, False

    def request(self, requests):
        msg = []
        for key, value in requests.iteritems():
            msg += [key, value]
        
        # send it to all servers
        seq = self.send(msg)
        
        # this function conglomer
        def validfunc(response):
            for request in requests:
                if request not in response:
                    return None
            return response

        # wait (with timeout) for the first response that matches the sequence number
        reply, valid = self.recv(seq, validfunc)
        if valid:
            return reply
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice test client")
    parser.add_argument('--request', action="append",
                        help="request key")
    parser.add_argument('--push', action="append",
                        help="push key:value (i.e. use colon as separator)")
    parser.add_argument('servers', nargs='+',
                        help="server(s)")
    args = parser.parse_args()

    client = Client(args.servers)
    requests = {}
    if args.request:
        for key in args.request:
            requests[key] = ''
    if args.push:
        for kvp in args.push:
            pair = kvp.split(':')
            requests[pair[0]] = pair[1]
    print client.request(requests)
    client.destroy()
