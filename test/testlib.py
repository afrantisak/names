import sys, os, time
import subprocess

def cmdstr(cmd):
    return ' '.join(cmd)
    
def python(cmd):
    return [sys.executable] + cmd

class Servers():
    def __init__(self, addresses):
        self.servers = []
        for index in xrange(len(addresses)):
            rotated = addresses[index:] + addresses[:index]
            self.servers.append(subprocess.Popen(python(['server.py'] + rotated)))
        time.sleep(1) # bit of a pause to synchronize things
            
    def kill(self):
        for server in self.servers:
            server.kill()

def Client(args, addresses):
    os.system(cmdstr(python(['client.py'] + args + addresses)))
    
def BasicTest(addresses):
    servers = Servers(addresses)
    Client(['--request=asdf'], addresses)
    Client(['--push=asdf:qwer'], addresses)
    Client(['--request=asdf'], addresses)
    servers.kill()

    

