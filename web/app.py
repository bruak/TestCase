from flask import jsonify, request, send_from_directory, render_template, redirect
from db import create_app
from websocket import websocket_init
import os
from auth import token_required
from dotenv import find_dotenv, dotenv_values

app = create_app()

app.static_folder = None

@app.route('/frontend/<path:path>')
def serve_frontend(path):
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    return send_from_directory(frontend_dir, path)

@app.route('/', methods=['GET'])
def root():
    return send_from_directory('.', 'frontend/html/login.html')



@app.route('/socket', methods=['GET'])
@token_required
def serve_testpage(current_user):
    return send_from_directory('.', 'frontend/html/websockettest.html')

socketio = websocket_init()  # WEBSOCKET

# .env configuration check
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    print(f".env file found at: {dotenv_path} ✓ ")
    env_vars = dotenv_values(dotenv_path)
    print(f"Found {len(env_vars)} environment variables")
    print(f"JWT_SECRET_KEY is {'set ✓ ' if 'JWT_SECRET_KEY' in env_vars else 'NOT set'}")
else:
    print(".env file NOT found!")

if __name__ == '__main__':
    cert_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), 'cerf'))
    cert_path = os.path.normpath(os.path.join(cert_dir, 'cert.pem'))
    key_path = os.path.normpath(os.path.join(cert_dir, 'key.pem'))
    
    cert_exists = os.path.exists(cert_path)
    key_exists = os.path.exists(key_path)
    
    if cert_exists and key_exists:
        print("Starting with HTTPS support (self-signed certificate)")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                    certfile=cert_path, keyfile=key_path)
    # Uncomment if you need fallback to HTTP
    # else:
    #     print("SSL certificate or key not found. Running without HTTPS. CONTACT YOUR IT ADMIN")
    #     socketio.run(app, host='0.0.0.0', port=5000, debug=True)



