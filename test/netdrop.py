import os
import sys
import testlib
sys.path.append("..")
import client

addresses = [
    'tcp://192.168.1.120:8000',
]

# this test requires sudo and only runs linux
# it brings the loopback down and back up in order to simulate a network failure
# TODO: netem?  write a testing loopback interface?  

def debug(response):
    return True

with testlib.Servers(addresses) as servers:

    # send first request, should return <none>
    cli = client.Client(addresses)
    msg = cli.gen_req(['asdf'])
    response = cli.sendrecv(msg, debug)
    print "received:"
    print client.pretty(response),
    
    print "Disconnect network, send definition"
    os.system('ifconfig lo down')
    
    # set a value, should echo back value
    push = client.Multimap()
    push['asdf'].add('qwer')
    msg = cli.gen_set(push)
    response = cli.sendrecv(msg)
    print "received:"
    print response
    print client.pretty(response),

    print "Reconnect network, query definition"
    os.system('ifconfig lo up')
    
    # request again, see if it gets the message it missed
    msg = cli.gen_req(['asdf'])
    response = cli.sendrecv(msg)
    print "received:"
    print client.pretty(response),
