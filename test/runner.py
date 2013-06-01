import sys, os

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
        
def python(args):
    cmd = [sys.executable] + args
    return os.system(' '.join(cmd))
    
def pythonref(args):
    # get first token; it must be the python script Name
    script = args[0]
    # compute the ref file name, must be same as python script name except .ref instead of .py
    ref = os.path.splitext(script)[0] + ".ref"
    # generate command to run the python script and compare output to the ref file
    cmd = [sys.executable] + args + ['|', 'diff', ref, '-']
    return os.system(' '.join(cmd))
        
def run(filename):
    abspath = os.path.abspath(filename)
    ret = 0
    for tokens, nLine, sLine in configfile(open(filename, 'r')):
        if len(tokens) < 2:
            print "Invalid file %s: must have at least 2 tokens in line #%d: '%s'" % (abspath, nLine, sLine)
            return 1
        args = tokens[1:]
        print args[0], '',
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
    parser.add_argument('filename',
                        help="tst filename")
    args = parser.parse_args()
    
    # TODO: use default runner.tst file and only override with --tst option
    # TODO: --reset-ref [testname] will re-write the .ref file for that test
    # TODO: --test-only [testname] will run only that test
    
    sys.exit(run(args.filename))
