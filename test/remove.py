import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--set=asdf:qwer'], addresses)

    # kill one server
    servers.kill(0)

    # make a request, should still work, since other one still running
    testlib.ClientCmdLine(['--get=asdf'], addresses)
    
    testlib.ClientCmdLine(['--set=asdf:_qwer'], addresses)
    
    servers.restart(0)
    
    testlib.ClientCmdLine(['--get=asdf'], addresses)
