import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
]

servers = testlib.Servers(addresses)
testlib.Client(['--push=asdf:qwer'], addresses)

#import sys
#sys.exit(0)

# kill one server
servers.servers[0].kill()

testlib.Client(['--request=asdf'], addresses)
servers.kill()
