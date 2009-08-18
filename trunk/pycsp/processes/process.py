"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import multiprocessing as mp
import ctypes
import cPickle as pickle
import sys

from channel import ChannelPoisonException, ChannelRetireException, Channel, ShmManager
from channelend import ChannelEndRead, ChannelEndWrite

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Decorators
def process(func):
    """
    @process decorator for creating process functions

    >>> @process
    ... def P():
    ...     pass

    >>> isinstance(P(), Process)
    True
    """
    if sys.platform == 'win32':
        raise Exception('The @process decorator is not supported in win32.')

    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

def io(func):
    """
    @io decorator for blocking io operations.
    In PyCSP.processes it has no effect, other than compatibility

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> sleep(0.01)
    """
    return func

# Classes
class Process(mp.Process):
    """ Process(...)
    """
    def __init__(self, fn, *args, **kwargs):
        mp.Process.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        # This reference is created to pass the ShmManager by inheritance.
        # It is required for PyCSP.processes to work in win32, since processes are not forked
        # but instead started in new python interpreters. Setting self.manager
        # here ensures, that the multiprocessing module pickles this instance and
        # recreates it in the new python interpreter.
        self.manager = ShmManager(allocate=True)

    def run(self):
        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            for ch in [x for x in self.args if isinstance(x, ChannelEndRead) or isinstance(x, ChannelEndWrite) or isinstance(x, Channel)]:
                ch.poison()
        except ChannelRetireException, e:
            # look for channel ends
            for ch_end in [x for x in self.args if isinstance(x, ChannelEndRead) or isinstance(x, ChannelEndWrite)]:
                # Ignore if try to retire an already retired channel end.
                try:
                    ch_end.retire()
                except ChannelRetireException:
                    pass


# Functions
def Parallel(*plist):
    """ Parallel(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)

    >>> @process
    ... def P2(cin):
    ...     for i in range(10):
    ...         cin()
    
    >>> C = [Channel() for i in range(10)]
    >>> Cin = map(IN, C)
    >>> Cout = map(OUT, C)
    
    >>> Parallel([P1(Cout[i], i) for i in range(10)],[P2(Cin[i]) for i in range(10)])
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)
    
    >>> C = Channel()
    >>> Spawn([P1(OUT(C), i) for i in range(10)])
    
    >>> L = []
    >>> cin = IN(C)
    >>> for i in range(100):
    ...    L.append(cin())
    
    >>> len(L)
    100
    """
    _parallel(plist, False)

def _parallel(plist, block = True):
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        p.start()

    if block:
        for p in processes:
            p.join()

def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])
    The Sequence construct returns when all given processes exit.
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout):
    ...     Sequence([Process(cout,i) for i in range(10)])
    
    >>> C = Channel()
    >>> Spawn(P1(OUT(C)))
    
    >>> L = []
    >>> cin = IN(C)
    >>> for i in range(10):
    ...    L.append(cin())
    
    >>> L
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    """
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        # Call Run directly instead of start() and join() 
        p.run()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
