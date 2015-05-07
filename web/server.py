from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit, send
import json
import sys

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('my event', namespace='/client')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    emit('my response', json, namespace='/client')

@socketio.on('update', namespace='/gdb')
def on_gdb_update(msg):
    data = json.loads(msg)
    print('Update: {}'.format(repr(data)))
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
