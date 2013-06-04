import sys, os, time
import subprocess

def cmdstr(cmd):
    return ' '.join(cmd)
    
def python(cmd):
    return [sys.executable] + cmd

class Servers():
    def __init__(self, addresses):
        self.addresses = addresses
        self.servers = []
        for index in xrange(len(addresses)):
            rotated = addresses[index:] + addresses[:index]
            self.servers.append(subprocess.Popen(python(['server.py'] + rotated)))
        time.sleep(3) # bit of a pause to synchronize things
    def kill(self, index):
        self.servers[index].kill()
    def restart(self, index):
        rotated = self.addresses[index:] + self.addresses[:index]
        self.servers[index] = subprocess.Popen(python(['server.py'] + rotated))
        time.sleep(3)
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        for server in self.servers:
            if server.returncode is None:
                server.kill()
            
def Client(args, addresses):
    os.system(cmdstr(python(['client.py'] + args + addresses)))
    
def BasicTest(addresses):
    with Servers(addresses) as servers:
        Client(['--request=asdf'], addresses)
        Client(['--push=asdf:qwer'], addresses)
        Client(['--request=asdf'], addresses)

    

