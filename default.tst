global:
    refdir: test
    
tests:
    basic:      ref python test/basic.py
    basic3:     ref python test/basic3.py
    death:      ref python test/death.py
    multreq:    ref python test/multreq.py
    latejoin:   ref python test/latejoin.py
    remove:     ref python test/remove.py
