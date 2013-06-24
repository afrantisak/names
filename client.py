import sys
import time
import zmq
import collections
import copy

class Multimap(collections.defaultdict):
    def __init__(self):
        super(Multimap, self).__init__(set)
        
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
        
def parse(msg_recv, values = Multimap()):
    union = Multimap()
    if len(msg_recv) and msg_recv[0] == 'DUMP':
        msg_recv = []
        union = values
    while len(msg_recv):
        cmd = msg_recv[0]
        key = msg_recv[1]
        value = msg_recv[2]
        msg_recv = msg_recv[3:]

        if cmd == 'SET':
            values[key].add(value)
            union.copy(values, key)
        if cmd == 'CLR':
            logging.debug("REMOVING: %s" % value[1:])
            values[key].remove(value[1:])
            if values[key].empty():
                values.remove(key)
            else:
                union.copy(values, key)
        if cmd == 'REQ':
            # do we know it?
            if key in values:
                union.copy(values, key)
            else:
                union[key].add('')
    return union

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
        
    def send(self, msg):
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
                    union = parse(msg)
                    if validfunc(union):
                        return union, True
        return union, False

    def gen_req(self, reqs):
        msg = []
        for key in reqs:
            msg += ['REQ', key, '']
        return msg
        
    def gen_set(self, sets):
        msg = []
        for key, values in sets.iteritems():
            for value in values:
                msg += ['SET', key, value]
        return msg
        
    def sendrecv(self, msg, validfunc = lambda response: True):
        # send it to all servers
        seq = self.send(msg)
        
#        # this function makes sure we got answers for all of our questions
#        def validfunc(response):
#            for request in requests:
#                if request not in response:
#                    return None
#            return response

        # wait (with timeout) for the first response that matches the sequence number
        #reply, valid = self.recv(seq, validfunc)
        reply, valid = self.recv(seq, validfunc)
        if valid:
            return reply
            
def pretty(data, indent='    '):
    if not data:
        return indent + "<none>\n"
    return data.prettyprint(indent)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nds test client")
    parser.add_argument('--request', action='append', 
                        help="request key")
    parser.add_argument('--push', action='append',
                        help="push key:value (i.e. use colon as separator)")
    parser.add_argument('--timeout', type=float, default=2.5,
                        help="timeout in seconds")
    parser.add_argument('servers', nargs='+',
                        help="server(s)")
    args = parser.parse_args()

    client = Client(args.servers, args.timeout)
    msg = []
    if args.request:
        msg += client.gen_req(args.request)
    if args.push:
        requests = Multimap()
        for kvp in args.push:
            pair = kvp.split(':')
            requests[pair[0]].add(pair[1])
            msg += client.gen_set(requests)
    response = client.sendrecv(msg)
    print "received:"
    print pretty(response),
    client.destroy()
