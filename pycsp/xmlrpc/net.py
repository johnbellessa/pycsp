"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Imports
import threading, sys

import xmlrpclib

from configuration import *
from alternation import *
from channel import *
from channelend import *
from guard import *
from pycsp.common.const import *

# Classes
class ClientManager(object):
    """
    ClientManageer is a singleton class.

    The purpose is the handle the connection to a nameserver and to
    create a ServerManager if necessary. This ServerManager runs
    as a process and functions as a channel server, handling all blocking
    communication.

    >>> A = ClientManager()
    >>> B = ClientManager()
    >>> A == B
    True
    """

    __instance = None  # the unique instance

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:

            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            cls.__instance.URI = Configuration().get(NET_SERVER_URI)
            if cls.__instance.URI == "":
                print 'ERROR: You are required to set the URI'
                print 'Example:'
                print 'Configuration().set(NET_SERVER_URI, "PYRO://127.0.1.1:7766/7f00010176411de57a4f70356b2ac5635e")'
                sys.exit(0)
            print 'URI', cls.__instance.URI
            cls.__instance.server = xmlrpclib.ServerProxy(cls.__instance.URI)

            # Found daemon
            

        return cls.__instance
    getInstance = classmethod(getInstance)


class Channel(object):
    """ Channel class with network support. Blocking communication
    """
    def __new__(cls, *args, **kargs):
        if kargs.has_key('buffer') and kargs['buffer'] > 0:
            import buffer                      
            chan = buffer.BufferedChannel(*args, **kargs)
            return chan
        else:
            return object.__new__(cls)

    def __init__(self, name=None, buffer=0):
        self.URI = ClientManager().URI
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        self.name = server.Channel(name)


    def _read(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        result = server.Channel_read(self.name)
        return result

    def _write(self, msg):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        result = server.Channel_write(self.name, msg)
        return result

    def poison(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        server.Channel_poison(self.name)

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    def reader(self):
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        server.Channel_join_reader(self.name)

    def leave_reader(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        server.Channel_leave_reader(self.name)

    def join_writer(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        server.Channel_join_writer(self.name)

    def leave_writer(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        server.Channel_leave_writer(self.name)

class Alternation:
    """
    Alternation class with XML-RPC support

    Alternation supports input and output guards. Guards are ChannelEnd
    or Guard objects.
    
    Note that alternation always performs the guard that was chosen,
    i.e. channel input or output is executed within the alternation so
    even the empty choice with an alternation execution or a choice where
    the results are simply ignored, still performs the guarded input or
    output.
    """
    def __init__(self, guards):
        self.id = None
        self.URI = ClientManager().URI

        # Preserve tuple entries and convert dictionary entries to tuple entries
        self.guards = []
        for g in guards:
            if type(g) == types.TupleType:
                self.guards.append(g)
            elif type(g) == types.DictType:
                for elem in g.keys():
                    if type(elem) == types.TupleType:
                        self.guards.append((elem[0], elem[1], g[elem]))
                    else:
                        self.guards.append((elem, g[elem]))

        # The internal representation of guards is a prioritized list
        # of tuples:
        #   input guard: (channel end, action) 
        #   output guard: (channel end, msg, action)

        # Default is to go one up in stackframe.
        self.execute_frame = -1

        # Replace channel end objects with channel name
        reduced_guards = []
        for g in self.guards:
            if len(g)==3:
                c, msg, action = g
                op = WRITE
            else:
                c, action = g
                msg = None
                op = READ
                
            if isinstance(c, Guard):
                c.g = None
                reduced_guards.append((c, op, msg))
            else:
                reduced_guards.append((c.channel.name, op, msg))

        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        self.id = server.Alternation(reduced_guards)

    def __del__(self):
        if not self.id == None:
            server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
            server.Alternation_delete(self.id)


    def set_execute_frame(self, steps):
        if steps > 0:
            self.execute_frame = -1*steps
        else:
            self.execute_frame = steps

    def choose(self):
        server = xmlrpclib.ServerProxy(self.URI, allow_none=True)
        result = server.Alternation_choose(self.id)
        return result        

    def execute(self):
        """
        Selects the guard and executes the attached action. Action is a function or python code passed in a string.
        """
        (idx, c, msg, op) = self.choose()
        if self.guards[idx]:
            action = self.guards[idx][-1]

            # Executing Choice object method
            if isinstance(action, Choice):
                if op==WRITE:
                    action.invoke_on_output()
                else:
                    action.invoke_on_input(msg)

            # Executing callback function object
            elif callable(action):
                # Choice function not allowed as callback
                if type(action) == types.FunctionType and action.func_name == '__choice_fn':
                    raise Exception('@choice function is not instantiated. Please use action() and not just action')
                else:
                    # Execute callback function
                    if op==WRITE:
                        action()
                    else:
                        action(channel_input=msg)

            # Compiling and executing string
            elif type(action) == types.StringType:
                # Fetch process frame and namespace
                processframe= inspect.currentframe()
                steps = self.execute_frame
                while (steps < 0):
                    processframe = processframe.f_back
                    steps += 1
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if op==READ:
                    f_locals.update({'channel_input':msg})

                # Execute action
                exec(code, f_globals, f_locals)

            elif type(action) == types.NoneType:
                pass
            else:
                raise Exception('Failed executing action: '+str(action))
    
        # Lookup real guard
        c = self.guards[idx][0]

        return (c, msg)

    def select(self):
        """
        Selects the guard.
        """

        idx, c, msg, op = self.choose()

        # Lookup real guard
        c = self.guards[idx][0]

        return (c, msg)
    


class InputGuard:
    def __init__(self, ch_end, action=None):
        if ch_end.op == READ:
            self.g = (ch_end, action)
        else:
            raise Exception('InputGuard requires an input ch_end')

class OutputGuard:
    def __init__(self, ch_end, msg, action=None):
        if ch_end.op == WRITE:
            self.g = (ch_end, msg, action)
        else:
            raise Exception('OutputGuard requires an output ch_end')

def AltSelect(*guards):
    L = []
    # Build guard list
    for item in guards:
        try:
            L.append(item.g)
        except AttributeError:
            raise Exception('Cannot use ' + str(item) + ' as guard. Only use *Guard types for AltSelect')

    a = Alternation(L)
    a.set_execute_frame(-2)
    return a.execute()
                

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
