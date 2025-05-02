from flask import jsonify, request, send_from_directory
from db import create_app
from websocket import websocket_init
import os
import auth
from dotenv import find_dotenv, dotenv_values

app = create_app()  # DB
socketio = websocket_init()  # WEBSOCKET

@app.route('/', methods=['GET'])
def root():
    return send_from_directory('.', 'frontend/html/websockettest.html')  


# .env'in yüklenmeden önce konumunu kontrol et
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    print(f".env file found at: {dotenv_path} ✓ ")
    # Değerleri görüntüle (hassas bilgileri göstermeden)
    env_vars = dotenv_values(dotenv_path)
    print(f"Found {len(env_vars)} environment variables")
    print(f"JWT_SECRET_KEY is {'set ✓ ' if 'JWT_SECRET_KEY' in env_vars else 'NOT set'}")
else:
    print(".env file NOT found!")


if __name__ == '__main__':
    cert_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), 'cerf'))
    cerf_path = os.path.normpath(os.path.join(cert_dir, 'cert.pem'))
    key_path = os.path.normpath(os.path.join(cert_dir, 'key.pem'))
    
    cerf_exists = os.path.exists(cerf_path)
    key_exists = os.path.exists(key_path)

    
    if os.path.exists(cerf_path) and os.path.exists(key_path):
        print("Starting with HTTPS support (self-signed certificate)")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                    certfile=cerf_path, keyfile=key_path)
    #lse:
    #   print("SSL certificate or key not found. Running without HTTPS. CONTANCT YOUR IT ADMIN")
    #   socketio.run(app, host='0.0.0.0', port=5000, debug=True) # ! LOCALHOST OLACAK
    #   app.debug = True # ! ITS FOR TEST
    
    