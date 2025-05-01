from flask import Flask, jsonify

app = Flask(__name__)

UserDb = { 
    "user": {
        "username": "admin",
        "password": "admin"
    }
}


@app.route('/')
def hello():
    return jsonify({"message": "BOYDAN AT"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
