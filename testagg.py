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
                if hasattr(self.proc, 'postprocess'):
                    out = out.split('\n')[:-1]
                    out = [line + '\n' for line in out]
                    self.proc.postprocess(out)
                elif out:
                    print out.rstrip()
        def kill(self):
            if self.proc:
                # kill with extreme prejudice
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
        def returncode(self):
            if self.proc:
                return self.proc.returncode
            elif self.proc == 0:
                return 0
            else:
                return 1
    return Timeout(Task(), timeout)
    
def run_cmd(cmd, timeout):
    def Proc(stdout, stdin, stderr):
        return subprocess.Popen(cmd, stdout=stdout, stdin=stdin, stderr=stderr, preexec_fn=os.setpgrp)
    return TimeoutProcess(Proc, timeout)

def run_cmd_ref(cmd, ref, refop, timeout):
    def Proc(stdout, stdin, stderr):
        if refop == 'gen':
            print "Generating %s" % ref,
            with open(ref, 'w') as out:
                return subprocess.Popen(cmd, stdout = out, preexec_fn=os.setpgrp)
        elif refop == 'ignore':
            return subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
        else:
            if not os.path.exists(ref):
                print "Ref file does not exist: %s" % ref
                return None
            if refop == 'dump':
                for line in open(ref, 'r'):
                    print line.rstrip()
                return 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
            def postprocess(out):
                import difflib
                diff = difflib.context_diff(open(ref, 'r').readlines(), out, "Expected", "Actual", n=2)
                for line in diff:
                    print line.rstrip()
            proc.postprocess = postprocess
            return proc
    return TimeoutProcess(Proc, timeout)

def run_python(args, timeout):
    cmd = [sys.executable] + args
    return run_cmd(cmd, timeout)
    
def run_python_ref(args, refop, timeout):
    # get first token; it must be the python script Name
    script = args[0]
    # ref file name must be same as python script name except add .ref
    ref = script + '.ref'
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args
    return run_cmd_ref(cmd, ref, refop, timeout)
    
def run_test(instruction, name, args, refop, timeout):
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
        ret = run_cmd_ref([name] + args, refop, timeout)
    elif instruction == 'python':
        ret = run_python([name] + args, timeout)
    elif instruction == 'python-ref':
        ret = run_python_ref([name] + args, refop, timeout)

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
        
def run(testfilename, tests, refop, timeout):
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
        
            aggregate |= run_test(instruction, name, args, refop, timeout)
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
    parser.add_argument('--ref', choices=['cmp', 'gen', 'ignore', 'dump'], default='cmp',
                        help="ref file operations (default=cmp)")
    parser.add_argument('--deftimeout', type=float, default=20,
                        help="default timeout in seconds")
    args = parser.parse_args()
    
    sys.exit(run(args.tstfile, args.tests, args.ref, args.deftimeout))
