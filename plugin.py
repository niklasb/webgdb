from __future__ import print_function
import json
import logging
import os
import six
import sys
import threading
import traceback
import types

from socketIO_client import SocketIO, BaseNamespace

FILE = os.path.abspath(os.path.expanduser(__file__))
if os.path.islink(FILE):
    FILE = os.readlink(FILE)
sys.path.append(os.path.join(os.path.dirname(FILE)))

import ezgdb
import util
ez = ezgdb.EzGdb()

SOCKETIO_HOST = '127.0.0.1'
SOCKETIO_PORT = 5000

def pack_num(num, word_size):
    hexed = hex(num)[2:].rstrip('L')
    return {
        'val': num,
        'hex': hexed,
        'hexPadded': hexed.rjust(word_size*2, '0'),
        'dec': str(num).rstrip('L'),
    }

def fix_numbers(obj, word_size):
    if isinstance(obj, six.integer_types):
        return pack_num(obj, word_size)
    elif isinstance(obj, types.DictType):
        return { k: fix_numbers(v, word_size) for k, v in obj.items()}
    elif isinstance(obj, (types.ListType, types.TupleType)):
        return [fix_numbers(x, word_size) for x in obj]
    return obj

class GdbWeb(object):
    def __init__(self, server_conn=None):
        self.views = []
        self.server = server_conn
        self.assembly_view = None
        self.data_views = [
            {
                'location': '$' + ez.get_stack_reg(),
                'unit': ez.get_bits() / 8,
                'count': 10,
            }
        ]

    def set_server_conn(self, server_conn):
        self.server = server_conn

    def compute_assembly_view(self, view):
        return ez.disassemble(view['location'], view['count'])

    def compute_data_view(self, view):
        unit = view['unit']
        count = view['count']
        addr = ez.eval_location(view['location'])
        data = ez.read(addr, unit * count)
        words = []
        for x in util.grouper(data, unit):
            val = util.unpack_le(x)
            words.append({
                'address': addr,
                'value': val,
                'smart': ez.make_smart(val),
            })
            addr += unit
        assert len(words) == count
        return words

    def view_with_result(self, view, f):
        view = dict(view.items())
        view['result'] = f(view)
        return view

    def adapt_assembly_view(self):
        ip = ez.get_ip()
        reset_to_ip = {'location': ip, 'count': 20}
        if not self.assembly_view:
            self.assembly_view = reset_to_ip
        ins = self.compute_assembly_view(self.assembly_view)
        if ip < ins[0]['address'] or ip + 10 >= ins[-1]['address']:
            self.assembly_view = reset_to_ip

    def send_state(self, state):
        self.server.emit('update', fix_numbers(state, ez.get_bits() / 8))

    def handle_change(self):
        print('Handle change')
        try:
            try:
                self.adapt_assembly_view()
                self.assembly_view = self.view_with_result(self.assembly_view,
                        self.compute_assembly_view)
                self.data_views = [
                    self.view_with_result(view, self.compute_data_view)
                    for view in self.data_views
                ]
            except gdb.MemoryError:
                # if handle_change is called from a thread, we can't read memory
                # for whatever reason. In that case, just use the old state.
                pass

            bps = [addr for num, addr in ez.get_breakpoints()]
            regs = ez.get_reginfo()
            for reg in regs:
                reg['smart'] = ez.make_smart(reg['value'])
            state = {
                'info': {
                    'bits': ez.get_bits(),
                    'breakpoints': bps,
                    'ip': ez.get_ip(),
                    'registers': regs,
                },
                'assemblyView': self.assembly_view,
                'dataViews': self.data_views,
            }
            self.send_state(state)
        except:
            traceback.print_exc(file=sys.stderr)

    def rpc_set_breakpoint(self, address):
        ez.set_breakpoint(int(address, 16))
        self.handle_change()

    def rpc_delete_breakpoint(self, address):
        ez.delete_breakpoint(int(address, 16))
        self.handle_change()

    def handle_rpc(self, rpc):
        try:
            getattr(self, 'rpc_' + rpc['method'])(**rpc['args'])
        except:
            traceback.print_exc(file=sys.stderr)

gdbweb = GdbWeb()

# set up socket.io client
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('socketIO_client').setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)
class GdbNamespace(BaseNamespace): pass
print('Connecting to web server...')
# TODO add timeout
io = SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
io_gdb = io.define(GdbNamespace, '/gdb')
print('Connected.')
gdbweb.set_server_conn(io_gdb)
io_gdb.on('rpc', gdbweb.handle_rpc)

# start message main loop
t = threading.Thread(target=lambda: io.wait())
t.daemon = True
t.start()

# set up GDB event handlers
gdb.events.stop.connect(lambda evt: gdbweb.handle_change())
