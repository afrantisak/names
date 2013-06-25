import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--set=asdf:qwer'], addresses)

    # kill one server, restart it, it should get a dump from the other one
    servers.kill(0)
    servers.restart(0)
    # now kill the other one.  The new one should still work
    servers.kill(1)

    # make a request, should still work, since one still running
    testlib.ClientCmdLine(['--get=asdf'], addresses)
