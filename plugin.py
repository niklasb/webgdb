from __future__ import print_function
import os
import sys

DEBUG = True
FILE = os.path.abspath(os.path.expanduser(__file__))
if os.path.islink(FILE):
    FILE = os.readlink(FILE)
sys.path.append(os.path.join(os.path.dirname(FILE), "lib"))

def cont_handler(evt):
    print("cont: %s" % repr(evt))

def stop_handler(evt):
    print("stop: %s" % repr(evt))

gdb.events.stop.connect(cont_handler)
gdb.events.cont.connect(stop_handler)
