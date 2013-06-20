import testlib

addresses = [
    'tcp://127.0.0.1:8000'
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--push=asdf:def1'], addresses)
    testlib.ClientCmdLine(['--push=asdf:def2'], addresses)
    testlib.ClientCmdLine(['--request=asdf'], addresses)
