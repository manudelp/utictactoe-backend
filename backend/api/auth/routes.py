from flask import request, jsonify
from . import auth_routes
from database import register_user, login_user, verify_token as db_verify_token

# REGISTER
@auth_routes.route('/register', methods=['POST'])
def register():
    """User registration using Supabase Auth."""
    data = request.json

    # Continue with registration logic
    if not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing required fields."}), 400

    # Register user with Supabase
    user = register_user(data['email'], data['password'], data['name'])
    
    if not user:
        return jsonify({"message": "Registration failed. Email might already be in use."}), 400

    return jsonify({"message": "User registered successfully!"}), 201

# LOGIN
@auth_routes.route('/login', methods=['POST'])
def login():
    """User login using Supabase Auth."""
    data = request.json

    # Continue with login logic
    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing email or password."}), 400

    # Login with Supabase Auth
    session, user = login_user(data['email'], data['password'])
    
    if not session or not user:
        return jsonify({"message": "Invalid credentials."}), 401

    return jsonify({
        "access_token": session.access_token,
        "name": user['name']
    }), 200

# VERIFY TOKEN
@auth_routes.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token using Supabase Auth."""
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({"message": "Token is missing."}), 401

    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Verify token with Supabase
        user = db_verify_token(token)
        
        if not user:
            return jsonify({"message": "Invalid token."}), 401
        
        return jsonify({"valid": True, "data": user}), 200
    except Exception as e:
        return jsonify({"message": f"Invalid token: {str(e)}"}), 401
