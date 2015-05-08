from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit, send
import json
import sys

app = Flask(__name__)
socketio = SocketIO(app)
gdb_state = {}

# client <-> webserver
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/client')
def on_client_connect():
    print('Client connected, sending state')
    emit('update', gdb_state['state'], namespace='/client')

@socketio.on('rpc', namespace='/client')
def on_rpc(data):
    emit('rpc', data, namespace='/gdb', broadcast=True)

# gdb <-> webserver
@socketio.on('update', namespace='/gdb')
def on_gdb_update(data):
    print('Updated GDB state')
    gdb_state['state'] = data
    emit('update', data, namespace='/client', broadcast=True)

# default config
config = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True,
    'log_file': None,
}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
    app.debug = config['debug']
    socketio.run(app,
        host=config['host'],
        port=config['port'],
        log_file=config['log_file'])
