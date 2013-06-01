import sys, os

def cmdstr(cmd):
    return ' '.join(cmd)
    
def python(cmd):
    return [sys.executable] + cmd
    
servers = [
    'tcp://127.0.0.1:8000'
]
    
import subprocess
server = subprocess.Popen(python(['server.py'] + servers))

os.system(cmdstr(python(['client.py', '--request=asdf'] + servers)))
os.system(cmdstr(python(['client.py', '--push=asdf:qwer'] + servers)))
os.system(cmdstr(python(['client.py', '--request=asdf'] + servers)))

server.kill()