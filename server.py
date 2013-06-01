import sys
import zmq

def run(server_addresses):
    context = zmq.Context()
    
    # the first address is us
    reply = context.socket(zmq.REP)
    print "Server:", server_addresses[0]
    reply.bind(server_addresses[0])
    
    # the rest are peers
    peers = context.socket(zmq.DEALER)
    for peer_address in server_addresses[1:]:
        peers.connect(peer_address)
        print "  Peer:", peer_address

    # data map
    values = {}

    while True:
        # wait for a message
        request = reply.recv_multipart()
        if not request:
            break  # Interrupted
        
        print request
        assert len(request) >= 4

        # parse message
        sequence = request[0]
        reqtype = request[1]
        key = request[2]
        value = request[3]

        # respond
        if reqtype == 'REQ':
            if key:
                # do we know it?
                if key in values:
                    # look up value and reply
                    value = values[key]
                else:
                    value = ''
                msg = [sequence, 'PUSH', key, value]
                reply.send_multipart(msg)
            else:
                pass
                # send all values
                #msg = [sequence, 'PUSH']
                #for key, value in values.iteritems():
                #    msg += [key, value]
            continue
        if reqtype == 'PUSH':
            # store value and sync
            # TODO: duplicate check
            values[key] = value
            msg = [sequence, 'OK', key, value]
            reply.send_multipart(msg)
            continue

    server.setsockopt(zmq.LINGER, 0)  # Terminate eaerly

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="nameservice server")
    parser.add_argument('servers', nargs='+',
                        help="server(s).  The first server address will be hosted.  The other addresses are peers")
    args = parser.parse_args()

    run(args.servers)
