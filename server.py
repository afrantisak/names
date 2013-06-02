import sys
import zmq
import collections

def run(server_addresses):
    context = zmq.Context()
    
    # the first address is us
    server = context.socket(zmq.REP)
    server.bind(server_addresses[0])
    print "Server:", server_addresses[0]
    
    # the rest are peers
    peers = context.socket(zmq.DEALER)
    for peer_address in server_addresses[1:]:
        peers.connect(peer_address)
        print "  Peer:", peer_address

    # data map
    values = collections.defaultdict(list)

    while True:
        # wait for a message
        msg_recv = server.recv_multipart()
        if not msg_recv:
            break  # Interrupted
        
        print msg_recv
        assert len(msg_recv) >= 3

        # parse message
        sequence = msg_recv[0]
        key = msg_recv[1]
        value = msg_recv[2]

        # if key is set, then it is either a push or a named request 
        if key:
            # if value is set, then it is a psh
            if value:
                # store value and sync
                values[key].append(value)
                msg_send = [sequence]
                for value in values[key]:
                    msg_send += [key, value]
                server.send_multipart(msg_send)
            else: # it is a request
                # do we know it?
                msg_send = [sequence]
                if key in values:
                    for value in values[key]:
                        msg_send += [key, value]
                else:
                    msg_send += [key, '']
                server.send_multipart(msg_send)
        else:
            # key not set, it is a request all
            msg_send = [sequence]
            for key in values.keys():
                for value in values[key]:
                    msg_send += [key, value]
            server.send_multipart(msg_send)

    server.setsockopt(zmq.LINGER, 0)  # Terminate early

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice server")
    parser.add_argument('servers', nargs='+',
                        help="server(s).  The first server address will be hosted.  The other addresses are peers")
    args = parser.parse_args()

    run(args.servers)
