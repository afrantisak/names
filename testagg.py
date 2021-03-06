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
                # if it has a postprocess attribute, it is a function to process the output
                if hasattr(self.proc, 'postprocess'):
                    out = out.split('\n')[:-1]
                    out = [line + '\n' for line in out]
                    self.ret = self.proc.postprocess(out)
                elif out:
                    print out.rstrip()
        def kill(self):
            if self.proc:
                # kill with extreme prejudice
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
        def returncode(self):
            if hasattr(self, 'ret'):
                return self.ret
            elif self.proc:
                return self.proc.returncode
            elif self.proc == 0:
                return 0
            else:
                return 1
    return Timeout(Task(), timeout)
    
def testProcess(cmd, ref, refop, timeout):
    def Proc(stdout, stdin, stderr):
        if refop == 'gen':
            print "Generating ref file %s" % ref,
            with open(ref, 'w') as out:
                return subprocess.Popen(cmd, stdout = out, preexec_fn=os.setpgrp)
        elif refop == 'none':
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
                ret = 0
                for line in diff:
                    print line.rstrip()
                    ret = 1
                return ret
            proc.postprocess = postprocess
            return proc
    return TimeoutProcess(Proc, timeout)

def test(name, instruction, cmd, refop, timeout, options):
    print name,
    sys.stdout.flush()
    
    # capture stdout
    old_stdout = sys.stdout
    sys.stdout = mystdout = cStringIO.StringIO()

    ref = name + ".ref"
    if 'refdir' in options:
        ref = os.path.join(options['refdir'], ref)
    
    # run the job
    ret = -1
    if instruction == 'cmd':
        ret = testProcess(cmd, '', 'none', timeout)
    elif instruction == 'ref':
        ret = testProcess(cmd, ref, refop, timeout)

    # uncapture stdout
    sys.stdout = old_stdout

    if ret == -1:
        print "Invalid instruction '%s'" % (instruction)
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
    
def recurse(data, tests, refop, timeout, options):
    aggregate = 0
    found = 0
    for key, value in data.iteritems():
        if type(value) == dict:
            cwd = os.path.abspath(os.getcwd())
            os.chdir(key)
            agg, found = recurse(value, tests, refop, timeout, options)
            aggregate |= agg
            found += found
            os.chdir(cwd)
            continue
        tokens = value.split()
        instruction = tokens[0]
        cmd = tokens[1:]
        
        if tests and key not in tests:
            continue
    
        aggregate |= test(key, instruction, cmd, refop, timeout, options)
        found += 1
    return aggregate, found
    
def parse(testfilename, tests, refop, timeout):
    abspath = os.path.abspath(testfilename)
    aggregate = 0
    found = 0
    data = yaml.safe_load(open(abspath, 'r'))
    options = {}
    if '.global' in data:
        options = data['.global']
        data.remove('.global')
    aggregate, found = recurse(data, tests, refop, timeout, options)
    if not found:
        print "No tests found"
    return aggregate
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="test aggregator")
    parser.add_argument('--testfile', default="testagg.yml",
                        help="test yaml filename")
    parser.add_argument('tests', nargs='*', 
                        help="run these tests only")
    parser.add_argument('--ref', choices=['cmp', 'gen', 'none', 'dump'], default='cmp',
                        help="ref file operations (default=cmp)")
    parser.add_argument('--deftimeout', type=float, default=20,
                        help="default timeout in seconds")
    args = parser.parse_args()
    
    sys.exit(parse(args.testfile, args.tests, args.ref, args.deftimeout))
