import sys
import zmq
import collections
import client

def run(server_addresses):
    context = zmq.Context()
    
    # the first address is us
    server = context.socket(zmq.REP)
    server.bind(server_addresses[0])

    # the rest are peers
    peers = client.Client(server_addresses[1:])
    
    # get initial dump from peers
    msg = []
    seq = peers.send(msg)
        
    # wait to get as many repsonses as we can before the timeout
    values, valid = peers.recv(seq, lambda response: False)

    print "Server:", server_addresses[0]

    while True:
        # wait for a message
        msg_recv = server.recv_multipart()
        if not msg_recv:
            break  # Interrupted
        
        assert msg_recv[0] == peers.protocol
        msg_recv = msg_recv[1:]

        # parse message
        sequence = msg_recv[0]
        msg_recv = msg_recv[1:]
        msg_send = [peers.protocol, sequence]

        if len(msg_recv) == 0:
            # key not set, it is a request all
            for key in values.keys():
                for value in values[key]:
                    msg_send += [key, value]
            
        while len(msg_recv):
            key = msg_recv[0]
            value = msg_recv[1]
            msg_recv = msg_recv[2:]

            # if value is set, then it is a psh
            if value:
                # store value and sync
                values[key].add(value)
                for value in values[key]:
                    msg_send += [key, value]
            else: # it is a request
                # do we know it?
                if key in values:
                    for value in values[key]:
                        msg_send += [key, value]
                else:
                    msg_send += [key, '']
        server.send_multipart(msg_send)

    server.setsockopt(zmq.LINGER, 0)  # Terminate early

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice server")
    parser.add_argument('servers', nargs='+',
                        help="server(s).  The first server address will be hosted.  The other addresses are peers")
    args = parser.parse_args()

    run(args.servers)
