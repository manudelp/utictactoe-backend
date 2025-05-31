import os
import json
import bcrypt
import jwt
import requests
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

auth_routes = Blueprint('auth', __name__)

DATA_FILE = 'users.json'
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')

def load_users():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

def generate_token(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def validate_recaptcha(token):
    if not token:
        return False
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": RECAPTCHA_SECRET_KEY, "response": token}
    )
    return response.json().get("success", False)

@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"message": "Invalid reCAPTCHA"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"message": "Missing required fields."}), 400

    users = load_users()
    if any(u["email"] == email for u in users):
        return jsonify({"message": "User already exists."}), 400

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": hashed_password
    }
    users.append(user)
    save_users(users)

    return jsonify({"message": "User registered successfully!"}), 201

@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"message": "Invalid reCAPTCHA"}), 400

    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"message": "Missing email or password."}), 400

    users = load_users()
    for user in users:
        if user["email"] == email and bcrypt.checkpw(password.encode(), user["password"].encode()):
            token = generate_token(user)
            return jsonify({"access_token": token, "name": user["name"]}), 200

    return jsonify({"message": "Invalid credentials."}), 401

@auth_routes.route('/verify-token', methods=['POST'])
def verify_token():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing."}), 401
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "data": decoded}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token."}), 401

@auth_routes.route('/verify-recaptcha', methods=['POST'])
def verify_recaptcha():
    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"success": False, "message": "Invalid reCAPTCHA"}), 400
    return jsonify({"success": True}), 200
