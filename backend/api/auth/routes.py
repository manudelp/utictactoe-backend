import os
import logging
import requests
import jwt
from flask import request, jsonify
from supabase import create_client
from dotenv import load_dotenv
from . import auth_routes

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Validate that required environment variables are set
logger.info(f"Environment loaded - SUPABASE_URL: {'✅ Present' if SUPABASE_URL else '❌ MISSING'}")
logger.info(f"Environment loaded - SUPABASE_SERVICE_KEY: {'✅ Present' if SUPABASE_SERVICE_KEY else '❌ MISSING'}")

SUPABASE_JWKS_URL = f"{SUPABASE_URL}/auth/v1/keys"
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def validate_recaptcha(token):
    if not RECAPTCHA_SECRET_KEY:
        return False
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": RECAPTCHA_SECRET_KEY, "response": token},
    )
    return response.json().get("success", False)

@auth_routes.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    recaptcha_token = data.get("recaptcha")
    if not recaptcha_token or not validate_recaptcha(recaptcha_token):
        return jsonify({"message": "Invalid reCAPTCHA"}), 400

    email = data.get("email")
    password = data.get("password")
    name = data.get("name") or data.get("username")

    if not all([email, password, name]):
        return jsonify({"message": "Missing required fields."}), 400

    result = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": { "data": { "name": name } }
    })
    if result.get("error"):
        return jsonify({"message": result["error"]["message"]}), 400

    return jsonify({"message": "User registered successfully!"}), 201

@auth_routes.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    recaptcha_token = data.get("recaptcha")
    if not recaptcha_token or not validate_recaptcha(recaptcha_token):
        return jsonify({"message": "Invalid reCAPTCHA"}), 400

    email = data.get("email")
    password = data.get("password")
    if not all([email, password]):
        return jsonify({"message": "Missing email or password"}), 400

    result = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    if result.get("error"):
        return jsonify({"message": result["error"]["message"]}), 401

    session = result.get("data", {}).get("session")
    user = result.get("data", {}).get("user")
    if not session or not user:
        return jsonify({"message": "Authentication failed"}), 401

    access_token = session.get("access_token")
    return jsonify({"access_token": access_token, "name": user.get("user_metadata", {}).get("name")}), 200

@auth_routes.route('/verify-token', methods=['POST', 'OPTIONS'])
def verify_token():
    if request.method == 'OPTIONS':
        return '', 204

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"message": "Invalid Authorization header."}), 401

    token = auth_header.split("Bearer ")[1]
    try:
        jwks = requests.get(SUPABASE_JWKS_URL).json().get("keys", [])
        public_keys = {k["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(k) for k in jwks}
        header = jwt.get_unverified_header(token)
        key = public_keys.get(header["kid"])
        if not key:
            return jsonify({"message": "Invalid token."}), 401

        decoded = jwt.decode(token, key=key, algorithms=["RS256"], audience="authenticated")
        return jsonify({"valid": True, "data": decoded}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired."}), 401
    except Exception:
        return jsonify({"message": "Invalid token."}), 401

@auth_routes.route('/verify-recaptcha', methods=['POST', 'OPTIONS'])
def verify_recaptcha():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"success": False, "message": "Invalid reCAPTCHA"}), 400
    return jsonify({"success": True}), 200
