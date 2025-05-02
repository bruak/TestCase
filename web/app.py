from flask import jsonify, request, send_from_directory
from db import create_app
from websocket import websocket_init
import os
import auth

app = create_app()  # DB
socketio = websocket_init()  # WEBSOCKET

@app.route('/', methods=['GET'])
def root():
    return send_from_directory('.', 'websockettest.html')  


if __name__ == '__main__':
    cert_path = os.path.join(os.path.dirname(__file__), 'cerf', 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'cerf', 'key.pem')
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("Starting with HTTPS support (self-signed certificate)")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                    certfile=cert_path, keyfile=key_path)
    else:
        print("SSL certificate or key not found. Running without HTTPS.")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
        app.debug = True