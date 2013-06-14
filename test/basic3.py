import testlib

addresses = [
    'tcp://127.0.0.1:8000',
    'tcp://127.0.0.1:8001',
    'tcp://127.0.0.1:8002'
]

with testlib.Servers(addresses) as servers:
    testlib.Client(['--request=asdf'], addresses)
    testlib.Client(['--push=asdf:qwer'], addresses)
    testlib.Client(['--request=asdf'], addresses)
