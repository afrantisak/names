import sys
import zmq
import collections
import client

import logging
logging.basicConfig(filename='nds_server.log', level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(process)X %(thread)X %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class StdoutIndenter():
    def __enter__(self):
        # capture stdout
        import cStringIO
        self.old_stdout = sys.stdout
        sys.stdout = self.mystdout = cStringIO.StringIO()

    def __exit__(self, type, value, traceback):
        # uncapture stdout
        sys.stdout = self.old_stdout

        # if there was anything printed to stdout, print it, nicely indented
        if self.mystdout.getvalue():
            for line in self.mystdout.getvalue().split('\n')[:-1]:
                print "   ", line.rstrip()

def run(server_addresses):
    context = zmq.Context()
    values = client.Multimap()
    
    # the first address is us
    server = context.socket(zmq.REP)
    server.bind(server_addresses[0])
    
    # the rest are peers
    if len(server_addresses) > 1:
        print "Querying peers:"
        with StdoutIndenter():
            peers = client.Client(server_addresses[1:])
            
            # request initial dump from all peers
            values = peers.request(['DUMP'])
            
    # print our host address to console
    print "Server:", server_addresses[0]
    sys.stdout.flush()

    # main loop
    while True:
        # wait for a message
        msg_recv = server.recv_multipart()
        
        # make a copy for logging purposes
        msg_recv_orig = msg_recv
        
        # determine the protocol
        protocol = ''
        if len(msg_recv) > 1:
            protocol = msg_recv[0]
            msg_recv = msg_recv[1:]
        if protocol == client.Client.protocol:
            # get the sequence number
            sequence = msg_recv[0]
            msg_recv = msg_recv[1:]
            
            # parse the rest of the message
            union = client.parse(msg_recv, values)
                        
            # construct the return message from the results of the parsing
            msg_send = [protocol, sequence]
            for key in union.keys():
                for value in union[key]:
                    msg_send += ['SET', key, value]
            
            # log it and send it back
            logmsg = str(msg_recv_orig) + " -> " + str(msg_send)
            logging.info(logmsg)
            #print logmsg
            #sys.stdout.flush()
            server.send_multipart(msg_send)
        else:
            # invalid protocol
            logging.error(str(msg_recv_orig) + ": Unknown protocol")

    server.setsockopt(zmq.LINGER, 0)  # Terminate early

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="network dictionary server")
    parser.add_argument('servers', nargs='+',
                        help="address(es).  The first address will be hosted.  The other addresses are peers")
    args = parser.parse_args()

    try:
        run(args.servers)
    except KeyboardInterrupt:
        print "INTERRUPTED"
