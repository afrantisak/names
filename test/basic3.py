import testlib

server_addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
    'tcp://127.0.0.1:8002'
]

testlib.BasicTest(server_addresses)
