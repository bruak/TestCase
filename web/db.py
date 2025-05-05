from createapp import *
from werkzeug.security import generate_password_hash
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    @app.route("/register", methods=["POST"]) # !ITS FOR TEST
    def register():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "User already exists"}), 409
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201

            
    @app.route("/users", methods=["GET"]) #! ITS FOR TEST
    def get_users():
        users = User.query.all()

        user_list = [{"id": user.id, "username": user.username} for user in users]
        return jsonify(user_list), 200

    return app

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)

