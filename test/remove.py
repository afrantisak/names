import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
]

with testlib.Servers(addresses) as servers:
    testlib.Client(['--push=asdf:qwer'], addresses)

    # kill one server
    servers.kill(0)

    # make a request, should still work, since other one still running
    testlib.Client(['--request=asdf'], addresses)
    
    testlib.Client(['--push=asdf:_qwer'], addresses)
    
    servers.restart(0)
    
    testlib.Client(['--request=asdf'], addresses)
