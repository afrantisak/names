import sys, os
import subprocess
import datetime
import threading
import signal
import cStringIO
import yaml

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
            if self.proc:
                out = self.proc.communicate()[0]
                if out:
                    print out.rstrip()
        def kill(self):
            if self.proc:
                # kill with extreme prejudice
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
        def returncode(self):
            if self.proc:
                return self.proc.returncode
            else:
                return 1
    return Timeout(Task(), timeout)
    
def run_cmd(cmd, timeout):
    def Proc(stdout, stdin, stderr):
        return subprocess.Popen(cmd, stdout=stdout, stdin=stdin, stderr=stderr, preexec_fn=os.setpgrp)
    return TimeoutProcess(Proc, timeout)

def run_cmd_ref(cmd, ref, genref, noref, timeout):
    def Proc(stdout, stdin, stderr):
        if genref:
            with open(ref, 'w') as out:
                return subprocess.Popen(cmd, stdout = out, preexec_fn=os.setpgrp)
        elif noref:
            return subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
        else:
            if not os.path.exists(ref):
                print "Ref file does not exist: %s" % ref
                return None
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
            diff = subprocess.Popen(['diff', ref, '-'], stdin=proc.stdout, stdout=stdout, stderr=stderr, 
                                    preexec_fn=lambda: os.setpgid(0, proc.pid))
            proc.stdout.close()
            return diff
    return TimeoutProcess(Proc, timeout)

def run_python(args, timeout):
    cmd = [sys.executable] + args
    return run_cmd(cmd, timeout)
    
def run_python_ref(args, genref, noref, timeout):
    # get first token; it must be the python script Name
    script = args[0]
    # ref file name must be same as python script name except add .ref
    ref = script + '.ref'
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args #+ ['|', 'diff', ref, '-']
    if genref:
        print "GENERATING REF",
    return run_cmd_ref(cmd, ref, genref, noref, timeout)
    
def run_test(instruction, name, args, genref, noref, timeout):
    print name,
    sys.stdout.flush()
    
    # capture stdout
    old_stdout = sys.stdout
    sys.stdout = mystdout = cStringIO.StringIO()

    # run the job
    ret = -1
    if instruction == 'cmd':
        ret = run_cmd([name] + args, timeout)
    elif instruction == 'cmd-ref':
        ret = run_cmd_ref([name] + args, genref, noref, timeout)
    elif instruction == 'python':
        ret = run_python([name] + args, timeout)
    elif instruction == 'python-ref':
        ret = run_python_ref([name] + args, genref, noref, timeout)

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
        
def run(testfilename, tests, genref, noref, timeout):
    abspath = os.path.abspath(testfilename)
    aggregate = 0
    data = yaml.safe_load(open(abspath, 'r'))
    if 'global' in data:
        if 'cwd' in data['global']:
            os.chdir(data['global']['cwd'])
    if 'tests' in data:
        found = 0
        for key, value in data['tests'].iteritems():
            tokens = value.split()
            instruction = tokens[0]
            name = tokens[1]
            args = tokens[2:]
            
            if tests and key not in tests:
                continue
        
            aggregate |= run_test(instruction, name, args, genref, noref, timeout)
            found += 1
        if not found:
            print "No tests found"
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
    parser.add_argument('--noref', default=False, action='store_true',
                        help="do not compare to ref files for those tests that use them")
    parser.add_argument('--deftimeout', type=float, default=20,
                        help="default timeout in seconds")
    args = parser.parse_args()
    
    sys.exit(run(args.tstfile, args.tests, args.genref, args.noref, args.deftimeout))
