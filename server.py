import sys
import zmq

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
    values = {}

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

        # if key is set, then it is either a named request or a push
        if key:
            if value:
                # store value and sync
                # TODO: duplicate value check?
                values[key] = value
                msg_send = [sequence, key, value]
                server.send_multipart(msg_send)
            else:
                # do we know it?
                if key in values:
                    # look up value and reply
                    value = values[key]
                else:
                    value = ''
                msg_send = [sequence, key, value]
                server.send_multipart(msg_send)
        else:
            # key not set, it is a request all TODO
            #msg_send = [sequence]
            #for key, value in values.iteritems():
            #    msg_send += [key, value]
            pass

    server.setsockopt(zmq.LINGER, 0)  # Terminate early

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice server")
    parser.add_argument('servers', nargs='+',
                        help="server(s).  The first server address will be hosted.  The other addresses are peers")
    args = parser.parse_args()

    run(args.servers)
