#!/bin/env python
# -*- coding: utf-8 -*-

#### Imports ####

import threading, Queue
import os
import sys
import pydoc
import optparse

#### Classes ####

class Option(optparse.Option):
    def _set_opt_strings(self, opts):
        for opt in opts:
            if len(opt) < 2:
                raise OptionError(
                    "invalid option string %r: "
                    "must be at least two characters long" % opt, self)
            elif len(opt) == 2:
                self._short_opts.append(opt)
            else:
                self._long_opts.append(opt)

class OptionParser(optparse.OptionParser):
    def _process_args(self, largs, rargs, values):
        while rargs:
            arg = rargs[0]
            if arg == "--":
                del rargs[0]
                return
            elif arg[0:2] == "--":
                self._process_long_opt(rargs, values)
            elif arg[:1] == "-" and len(arg) > 1:
                if len(arg) > 2:
                    self._process_long_opt(rargs, values)
                else:
                    self._process_short_opts(rargs, values)
            elif self.allow_interspersed_args:
                largs.append(arg)
                del rargs[0]
            else:
                return 

class OptionGroup(optparse.OptionGroup):
    pass

#### Defines ####

def threaded(f, daemon=False):
    """This is a decorator, it returns a thread. To get the output use .result_queue.get()"""

    def wrapped_f(q, *args, **kwargs):
        '''this function calls the decorated function and puts the 
        result in a queue'''
        try:
            ret = f(*args, **kwargs)
            q.put(ret)
        except:
            print "Unexpected error:"
            for info in sys.exc_info():
                print info
            q.put(None)
            

    def wrap(*args, **kwargs):
        '''this is the function returned from the decorator. It fires off
        wrapped_f in a new thread and returns the thread object with
        the result queue attached'''

        q = Queue.Queue()

        t = threading.Thread(target=wrapped_f, args=(q,)+args, kwargs=kwargs)
        t.daemon = daemon
        t.start()
        t.result_queue = q        
        return t

    return wrap

def terminalSize(fd=1):
    """
    Returns height and width of current terminal. First tries to get
    size via termios.TIOCGWINSZ, then from environment. Defaults to 25
    lines x 80 columns if both methods fail.

    :param fd: file descriptor (default: 1=stdout)
    """
    try:
        import fcntl, termios, struct
        hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        try:
            hw = (os.environ['LINES'], os.environ['COLUMNS'])
        except:  
            hw = (25, 80)

    return hw

def terminalHeight(fd=1):
    """
    Returns height of terminal if it is a tty, 999 otherwise

    :param fd: file descriptor (default: 1=stdout)
    """
    if os.isatty(fd):
        height = terminalSize(fd)[0]
    else:
        height = 999
   
    return height

def politePrint(to_print):
    if terminalHeight()*1.5 < len(to_print):
        pydoc.pager(to_print)
    else:
        print to_print

#### Main ####

if __name__ == '__main__':
    print "This is a lib file, don't call it directly"
    exit(1)
