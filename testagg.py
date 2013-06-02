import sys, os
import subprocess
import datetime
import threading
import signal

def configfile(file):
    nLine = 0
    for line in file:
        nLine += 1
        if line and line[0] == '#':
            continue
        tokens = line.split()
        if len(tokens) == 0:
            continue
        yield tokens, nLine, line.rstrip()
        
def Timeout(task, timeout):
    thread = threading.Thread(target=task.run)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        print "TIMED OUT"
        task.kill()
    return task.returncode()
    
def run_timeout(cmd, timeout = 20):
    class Task():
        def __init__(self, cmd):
            self.cmd = cmd
        def run(self):
            self.proc = subprocess.Popen(self.cmd)
            self.proc.communicate()
        def kill(self):
            # kill with extreme prejudice
            os.killpg(os.getpgid(self.proc.pid), signal.SIGHUP)            
        def returncode(self):
            return self.proc.returncode
    return Timeout(Task(cmd), timeout)

def run_timeout_ref(cmd, ref, genref, timeout = 20):
    class Task():
        def __init__(self, cmd, ref, genref):
            self.cmd = cmd
            self.ref = ref
            self.genref = genref
        def run(self):
            if self.genref:
                with open(self.ref, 'w') as out:
                    self.proc = subprocess.Popen(self.cmd, stdout = out)
                    self.proc.communicate()
            else:
                proc = subprocess.Popen(self.cmd, stdout = subprocess.PIPE)
                self.proc = subprocess.Popen(['diff', self.ref, '-'], stdin = proc.stdout)
                proc.stdout.close()
                self.proc.communicate()
        def kill(self):
            # kill with extreme prejudice
            os.killpg(os.getpgid(self.proc.pid), signal.SIGHUP)            
        def returncode(self):
            return self.proc.returncode
    return Timeout(Task(cmd, ref, genref), timeout)

def python(args):
    cmd = [sys.executable] + args
    return run_timeout(cmd)
    
def pythonref(args, genref):
    # get first token; it must be the python script Name
    script = args[0]
    # compute the ref file name, must be same as python script name except .ref instead of .py
    ref = os.path.splitext(script)[0] + ".ref"
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args + ['|', 'diff', ref, '-']
    if genref:
        print "GENERATING REF",
    return run_timeout_ref(cmd, ref, genref)
        
def run(testfilename, tests, genref):
    abspath = os.path.abspath(testfilename)
    ret = 0
    for tokens, nLine, sLine in configfile(open(abspath, 'r')):
        if len(tokens) < 2:
            print "Invalid file %s: must have at least 2 tokens in line #%d: '%s'" % (abspath, nLine, sLine)
            return 1
        args = tokens[1:]
        if tests and args[0] not in tests:
            continue
        print args[0],
        sys.stdout.flush()
        if tokens[0] == 'python':
            ret |= python(args)
        elif tokens[0] == 'python-ref':
            ret |= pythonref(args, genref)
        else:
            print "Invalid file %s: invalid instruction '%s' in line #%d: '%s'" % (abspath, tokens[0], nLine, sLine)
        if ret:
            print "FAIL"
        else:
            print "ok"
    return 0
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="test runner")
    parser.add_argument('--tstfile', default="default.tst",
                        help="tst filename")
    parser.add_argument('tests', nargs='?',
                        help="run these tests only")
    parser.add_argument('--genref', default=False, action='store_true',
                        help="(re)generate *.ref files for those tests that use them")
    args = parser.parse_args()
    
    # TODO: use YAML or some other std file format reader
    # TODO: capture test output, show it nicely, and ONLY if something fails
    
    sys.exit(run(args.tstfile, args.tests, args.genref))
