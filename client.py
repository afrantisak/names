import sys
import time
import zmq
import collections
import copy

class Multimap(collections.defaultdict):
    def __init__(self):
        super(Multimap, self).__init__(set)
        
    def copyall(self, other):
        #self = copy.copy(other)
        self = other
        
    def copy(self, other, key):
        for value in other[key]:
            self[key].add(value)
        
    def prettyprint(self, indent='    '):
        s = ''
        for k, v in super(Multimap, self).iteritems():
            s += indent + k + ":\n"
            for value in v:
                s += indent + indent + value + "\n"
        return s
        
class SendMessage():
    def __init__(self, protocol, sequence):
        self.msg = [protocol, sequence]
        
    def add(self, multimap):
        for key in multimap.keys():
            for value in multimap[key]:
                self.msg += [key, value]
                
    def get(self):
        return self.msg
        
class Client():
    protocol = 'nds01'
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
        
    def send(self, msg = []): # default message is a request all
        self.sequence += 1
        msg = ['', Client.protocol, str(self.sequence)] + msg
        # send the request to all connected servers
        for server in xrange(len(self.server_addresses)):
            self.socket.send_multipart(msg)
        return self.sequence
            
    def recv(self, sequence, validfunc):
        # wait (with timeout) for responses that match the sequence number until validfunc returns valid dict
        union = Multimap()
        endtime = time.time() + self.timeout
        while time.time() < endtime:
            socks = dict(self.poll.poll((endtime - time.time())))
            if socks.get(self.socket) == zmq.POLLIN:
                msg = self.socket.recv_multipart()
                assert msg[1] == Client.protocol
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
            for v2 in value:
                msg += [key, v2]
        
        # send it to all servers
        seq = self.send(msg)
        
        # this function makes sure we got answers for all of our questions
        def validfunc(response):
            for request in requests:
                if request not in response:
                    return None
            return response

        # wait (with timeout) for the first response that matches the sequence number
        reply, valid = self.recv(seq, validfunc)
        if valid:
            return reply
            
def prettyprint(data, indent='    '):
    if not data:
        return indent + "<none>"
    return data.prettyprint(indent)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nds test client")
    parser.add_argument('--request', action='append', 
                        help="request key")
    parser.add_argument('--push', action='append',
                        help="push key:value (i.e. use colon as separator)")
    parser.add_argument('servers', nargs='+',
                        help="server(s)")
    args = parser.parse_args()

    client = Client(args.servers)
    requests = Multimap()
    if args.request:
        for key in args.request:
            requests[key].add('')
    if args.push:
        for kvp in args.push:
            pair = kvp.split(':')
            requests[pair[0]].add(pair[1])
    response = client.request(requests)
    print "received:"
    print prettyprint(response),
    client.destroy()
