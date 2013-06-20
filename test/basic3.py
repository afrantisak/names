import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
    'tcp://127.0.0.1:8002'
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--request=asdf'], addresses)
    testlib.ClientCmdLine(['--push=asdf:qwer'], addresses)
    testlib.ClientCmdLine(['--request=asdf'], addresses)
