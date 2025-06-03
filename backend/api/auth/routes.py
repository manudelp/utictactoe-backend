import os
import json
import bcrypt
import jwt
import requests
from flask import request, jsonify
from datetime import datetime, timedelta
from pathlib import Path

from . import auth_routes  # This imports the blueprint from __init__.py

BASE_DIR = Path(__file__).parent.parent.parent  # Gets the backend directory
DATA_FILE = os.path.join(BASE_DIR, 'users.json')

def get_secret_key():
    return os.getenv('JWT_SECRET_KEY')

def get_recaptcha_secret_key():
    return os.getenv('RECAPTCHA_SECRET_KEY')

def load_users():
    try:
        if not os.path.exists(DATA_FILE):
            print(f"Creating new users file at {DATA_FILE}")
            # Create the file with an empty array
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)
            return []
        with open(DATA_FILE, 'r') as f:
            users = json.load(f)
            print(f"Loaded {len(users)} users from {DATA_FILE}")
            return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_users(users):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(users, f)
            print(f"Saved {len(users)} users to {DATA_FILE}")
    except Exception as e:
        print(f"Error saving users: {e}")

def generate_token(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, get_secret_key(), algorithm="HS256")

def validate_recaptcha(token):
    secret = get_recaptcha_secret_key()
    if not secret:
        print("ERROR: Missing RECAPTCHA_SECRET_KEY in environment variables")
        return False

    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": secret, "response": token}
    )
    print("reCAPTCHA response:", response.json())
    return response.json().get("success", False)

@auth_routes.route('/register', methods=['POST'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    print(f"Registration attempt with data keys: {list(data.keys())}")
    
    # Check if recaptcha is present
    recaptcha_token = data.get("recaptcha")
    if not recaptcha_token:
        return jsonify({"message": "reCAPTCHA token is required"}), 400
    
    if not validate_recaptcha(recaptcha_token):
        return jsonify({"message": "Invalid reCAPTCHA. Please try again."}), 400

    # Accept either "name" or "username" for compatibility
    name = data.get("name") or data.get("username")
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

@auth_routes.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        print(f"Login attempt for email: {data.get('email')}")
        
        # Check recaptcha
        recaptcha_token = data.get("recaptcha")
        if not recaptcha_token:
            print("No recaptcha token provided")
            return jsonify({"message": "reCAPTCHA verification required"}), 400
            
        if not validate_recaptcha(recaptcha_token):
            print("Invalid recaptcha")
            return jsonify({"message": "Invalid reCAPTCHA"}), 400

        email = data.get("email")
        password = data.get("password")

        if not all([email, password]):
            return jsonify({"message": "Missing email or password"}), 400

        users = load_users()
        for user in users:
            if user["email"] == email:
                try:
                    if bcrypt.checkpw(password.encode(), user["password"].encode()):
                        token = generate_token(user)
                        print(f"Login successful for {email}")
                        return jsonify({"access_token": token, "name": user["name"]}), 200
                except Exception as e:
                    print(f"Password verification error: {e}")
                    return jsonify({"message": "Authentication error"}), 500
                    
                return jsonify({"message": "Invalid password"}), 401
                
        return jsonify({"message": "User not found"}), 401
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "An error occurred during login"}), 500

@auth_routes.route('/verify-token', methods=['POST', 'OPTIONS'])
def verify_token():
    if request.method == 'OPTIONS':
        return '', 204

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Invalid Authorization header."}), 401

    token = auth_header.split("Bearer ")[1]

    if not token:
        return jsonify({"message": "Token is missing."}), 401
    try:
        decoded = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        return jsonify({"valid": True, "data": decoded}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token."}), 401

@auth_routes.route('/verify-recaptcha', methods=['POST', 'OPTIONS'])
def verify_recaptcha():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"success": False, "message": "Invalid reCAPTCHA"}), 400
    return jsonify({"success": True}), 200
