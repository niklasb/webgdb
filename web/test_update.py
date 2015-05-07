import json
from socketIO_client import Socket

class GdbNamespace(BaseNamespace):
    def on_update_response(self, *args):
        print('on_update_response', args)

io = SocketIO('localhost', 5000)
ns = io.define(GdbNamespace, '/gdb')
state = {
    'bits': 64,
    'assembly': {
        'instructions': [
            {
                'address': 0x1000,
                'label': 'main',
                'mnemonic': 'mov',
                'op_str': 'eax, edx',
            },
            {
                'address': 0x1005,
                'label': 'main+5',
                'mnemonic': 'add',
                'op_str': 'eax, 5',
            },
        ],
    },
    'breakpoints': [0x1005],
    'ip': 0x1005,
    'registers': {
    },
}
ns.emit('update', json.dumps(state))
