import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
]

with testlib.Servers(addresses) as servers:
    testlib.Client(['--push=asdf:qwer', '--push=zxcv:uiop'], addresses)

    # kill one server
    servers.servers[0].kill()

    # make a request, should still work, since other one still running
    testlib.Client(['--request=asdf', '--request=zxcv'], addresses)
