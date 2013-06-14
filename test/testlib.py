import sys, os, time
import subprocess

def cmdstr(cmd):
    return ' '.join(cmd)
    
def python(cmd):
    return [sys.executable] + cmd

def WaitForLine(proc, expected):
    import fcntl, select
    fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, fcntl.fcntl(proc.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)    
    while proc.poll() == None:
        readx = select.select([proc.stdout.fileno()], [], [])[0]
        if readx:
            chunk = proc.stdout.read().rstrip()
            #print chunk
            for line in chunk.split('\n'):
                if line == expected:
                    return
            continue
            
class Servers():
    def __init__(self, addresses):
        self.addresses = addresses
        self.servers = []
        for index in xrange(len(addresses)):
            rotated = addresses[index:] + addresses[:index]
            cmd = python(['../server.py'] + rotated)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.address = addresses[index]
            self.servers.append(proc)
        for server in self.servers:
            WaitForLine(server, "Server: " + server.address)
    def kill(self, index):
        self.servers[index].kill()
    def restart(self, index):
        rotated = self.addresses[index:] + self.addresses[:index]
        self.servers[index] = subprocess.Popen(python(['../server.py'] + rotated))
        time.sleep(3)
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        for server in self.servers:
            if server.returncode is None:
                server.kill()
            
def Client(args, addresses):
    os.system(cmdstr(python(['../client.py'] + args + addresses)))
