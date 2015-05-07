from __future__ import print_function
import json
import logging
import os
import sys
import traceback

from socketIO_client import SocketIO, BaseNamespace

FILE = os.path.abspath(os.path.expanduser(__file__))
if os.path.islink(FILE):
    FILE = os.readlink(FILE)
sys.path.append(os.path.join(os.path.dirname(FILE)))

import ezgdb

ez = ezgdb.EzGdb(gdb)

# set up socket.io client
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('socketIO_client').setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)
class GdbNamespace(BaseNamespace):
    pass
io = SocketIO('127.0.0.1', 5000)
io_gdb = io.define(GdbNamespace, '/gdb')

def update_state(state):
    io_gdb.emit('update', json.dumps(state))

# set up event handlers
def cont_handler(evt):
    print('cont: %s' % repr(evt))

def on_change():
    bits = ez.get_bits()
    ip = ez.get_ip()
    breakpoints = ez.get_breakpoints()
    regs = ez.get_registers()
    ins = ez.disassemble(ip, 20)
    state = {
        'bits': bits,
        'assembly': { 'instructions': ins },
        'breakpoints': breakpoints,
        'ip': ip,
        'registers': regs,
    }
    update_state(state)

def stop_handler(evt):
    try:
        on_change()
    except:
        traceback.print_exc(file=sys.stderr)

gdb.events.cont.connect(cont_handler)
gdb.events.stop.connect(stop_handler)
#print(ez.get_arch())
#print(ez.get_stack_reg())
#print(ez.get_ip_reg())
#print(ez.get_breakpoints())
#regs = ez.get_registers()
#print(regs)
#ip = regs[ez.get_ip_reg()]
#print(ip)
#print(ez.disassemble(0x7ffff7b00810, 10))
