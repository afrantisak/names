import sys, os
import subprocess
import datetime
import threading
import signal
import cStringIO

# TODO: use YAML or some other std file format reader

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
        
def Timeout(task, seconds):
    thread = threading.Thread(target=task.run)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        print "TIMED OUT"
        task.kill()
    return task.returncode()
    
def TimeoutProcess(procfunc, timeout):
    class Task():
        def run(self):
            self.proc = procfunc(subprocess.PIPE, None, subprocess.STDOUT)
            out = self.proc.communicate()[0]
            if out:
                print out.rstrip()
        def kill(self):
            # kill with extreme prejudice
            os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
        def returncode(self):
            return self.proc.returncode
    return Timeout(Task(), timeout)
    
def run_cmd(cmd, timeout):
    def Proc(stdout, stdin, stderr):
        return subprocess.Popen(cmd, stdout=stdout, stdin=stdin, stderr=stderr, preexec_fn=os.setpgrp)
    return TimeoutProcess(Proc, timeout)

def run_cmd_ref(cmd, ref, genref, timeout):
    def Proc(stdout, stdin, stderr):
        if genref:
            with open(ref, 'w') as out:
                return subprocess.Popen(cmd, stdout = out, preexec_fn=os.setpgrp)
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
            diff = subprocess.Popen(['diff', ref, '-'], stdin=proc.stdout, stdout=stdout, stderr=stderr, 
                                    preexec_fn=lambda: os.setpgid(0, proc.pid))
            proc.stdout.close()
            return diff
    return TimeoutProcess(Proc, timeout)

def run_python(args, timeout):
    cmd = [sys.executable] + args
    return run_cmd(cmd, timeout)
    
def run_python_ref(args, genref, timeout):
    # get first token; it must be the python script Name
    script = args[0]
    # compute the ref file name, must be same as python script name except .ref instead of .py
    ref = os.path.splitext(script)[0] + ".ref"
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args + ['|', 'diff', ref, '-']
    if genref:
        print "GENERATING REF",
    return run_cmd_ref(cmd, ref, genref, timeout)
    
def run_test(instruction, name, args, genref, timeout):
    print name,
    sys.stdout.flush()
    
    # capture stdout
    old_stdout = sys.stdout
    sys.stdout = mystdout = cStringIO.StringIO()

    # run the job
    ret = -1
    if instruction == 'python':
        ret = run_python([name] + args, timeout)
    elif instruction == 'python-ref':
        ret = run_python_ref([name] + args, genref, timeout)

    # uncapture stdout
    sys.stdout = old_stdout

    if ret == -1:
        print "Invalid file %s: invalid instruction '%s' in line #%d: '%s'" % (abspath, instruction, nLine, sLine)
    elif ret:
        print "FAILED"
    else:
        print "ok"

    # if there was anything printed to stdout, print it, nicely indented
    if mystdout.getvalue():
        for line in mystdout.getvalue().split('\n'):
            print "   ", line.rstrip()
            
    if ret is None:
        return 127
    return ret
        
def run(testfilename, tests, genref, timeout):
    abspath = os.path.abspath(testfilename)
    aggregate = 0
    for tokens, nLine, sLine in configfile(open(abspath, 'r')):
        if len(tokens) < 2:
            print "Invalid file %s: must have at least 2 tokens in line #%d: '%s'" % (abspath, nLine, sLine)
            return 1
        
        instruction = tokens[0]
        name = tokens[1]
        args = tokens[2:]

        # filter on tests
        if tests and name not in tests:
            continue
        
        aggregate |= run_test(instruction, name, args, genref, timeout)
    return aggregate
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="test runner")
    parser.add_argument('--tstfile', default="default.tst",
                        help="tst filename")
    parser.add_argument('tests', nargs='?',
                        help="run these tests only")
    parser.add_argument('--genref', default=False, action='store_true',
                        help="(re)generate *.ref files for those tests that use them")
    parser.add_argument('--deftimeout', type=float, default=20,
                        help="default timeout in seconds")
    args = parser.parse_args()
    
    sys.exit(run(args.tstfile, args.tests, args.genref, args.deftimeout))
