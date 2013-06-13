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
    
    # the first address is us
    server = context.socket(zmq.REP)
    server.bind(server_addresses[0])
    
    values = client.Client.empty()

    # the rest are peers
    if len(server_addresses) > 1:
        print "Querying peers:"
        with StdoutIndenter():
            peers = client.Client(server_addresses[1:])
            
            # request initial dump from all peers
            seq = peers.send()
                
            # wait to get as many repsonses as we can before the timeout 
            # (ignore valid flag - we know it will be false)
            values, valid = peers.recv(seq, lambda response: False)

    # print our host address to console
    print "Server:", server_addresses[0]
    sys.stdout.flush()

    # main loop
    while True:
        # wait for a message
        msg_recv = server.recv_multipart()
        if not msg_recv:
            break  # Interrupted
        
        msg_recv_orig = msg_recv
        if len(msg_recv) > 1:
            protocol = msg_recv[0]
        if protocol == client.Client.protocol:
            msg_recv = msg_recv[1:]

            # parse message
            sequence = msg_recv[0]
            msg_recv = msg_recv[1:]
            msg_send = [protocol, sequence]

            if len(msg_recv) == 0:
                # key not set, it is a request all
                for key in values.keys():
                    for value in values[key]:
                        msg_send += [key, value]
            while len(msg_recv):
                key = msg_recv[0]
                value = msg_recv[1]
                msg_recv = msg_recv[2:]

                # if value is set, then it is a push
                if value:
                    # store or remove value
                    if value[0] == '_':
                        logging.debug("REMOVING: %s" % value[1:])
                        values[key].remove(value[1:])
                    else:
                        values[key].add(value)
                    # send response
                    for value in values[key]:
                        msg_send += [key, value]
                else: # it is a request
                    # do we know it?
                    if key in values:
                        for value in values[key]:
                            msg_send += [key, value]
                    else:
                        msg_send += [key, '']
        
            logging.info(str(msg_recv_orig) + " -> " + str(msg_send))
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

    run(args.servers)
