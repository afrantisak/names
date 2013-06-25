import testlib

addresses = [
    'tcp://127.0.0.1:8000'
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--get=asdf'], addresses)
    testlib.ClientCmdLine(['--set=asdf:qwer'], addresses)
    testlib.ClientCmdLine(['--get=asdf'], addresses)
