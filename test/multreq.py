import testlib

addresses = [
    'tcp://127.0.0.1:8000',
]

with testlib.Servers(addresses) as servers:
    testlib.ClientCmdLine(['--set=asdf:qwer', '--set=zxcv:uiop'], addresses)
    testlib.ClientCmdLine(['--get=asdf', '--get=zxcv'], addresses)
