import testlib

addresses = [
    'tcp://127.0.0.1:8000'
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--set=asdf:def1'], addresses)
    testlib.ClientCmdLine(['--set=asdf:def2'], addresses)
    testlib.ClientCmdLine(['--get=asdf'], addresses)
