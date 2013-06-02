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
        
def time_delta(lhs, rhs):
    delta = lhs - rhs
    return delta.seconds + delta.microseconds/1E6    
        
def run_timeout(cmd, timeout = 20):
    proc = subprocess.Popen(cmd)
    time_start = datetime.datetime.now()
    while proc.returncode is None and time_delta(datetime.datetime.now(), time_start) < timeout:
        proc.poll()
    if proc.returncode is None:
        proc.kill()
        print "TIMED OUT"
        return 127
    return proc.returncode
        
class Timeout():
    def __init__(self, cmd, ref, timeout):
        self.cmd = cmd
        self.ref = ref
        self.diff = None
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        self.thread.join(timeout)
        if self.thread.is_alive():
            print "TIMED OUT"
            # kill with extreme prejudice
            os.killpg(os.getpgid(self.diff.pid), signal.SIGHUP)
            self.thread.join()
        self.returncode = self.diff.returncode
    def run(self):
        proc = subprocess.Popen(self.cmd, stdout = subprocess.PIPE)
        self.diff = subprocess.Popen(['diff', self.ref, '-'], stdin = proc.stdout)
        proc.stdout.close()
        self.diff.communicate()

def run_timeout_ref(cmd, ref, timeout = 20):
    proc = Timeout(cmd, ref, timeout)
    return proc.returncode

def python(args):
    cmd = [sys.executable] + args
    return run_timeout(cmd)
    
def pythonref(args):
    # get first token; it must be the python script Name
    script = args[0]
    # compute the ref file name, must be same as python script name except .ref instead of .py
    ref = os.path.splitext(script)[0] + ".ref"
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args + ['|', 'diff', ref, '-']
    return run_timeout_ref(cmd, ref)
        
def run(testfilename, tests):
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
            ret |= pythonref(args)
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
                        help="run these tests")
    args = parser.parse_args()
    
    # TODO: --reset-ref [testname] will re-write the .ref file for that test
    # TODO: use YAML file format
    # TODO: capture test output, show it nicely, and ONLY if something fails
    
    sys.exit(run(args.tstfile, args.tests))
