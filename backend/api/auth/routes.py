import os
import logging
import requests
import jwt
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from supabase import create_client
from dotenv import load_dotenv
from . import auth_routes

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

logger.info(f"Environment loaded - SUPABASE_URL: {'✅ Present' if SUPABASE_URL else '❌ MISSING'}")
logger.info(f"Environment loaded - SUPABASE_SERVICE_KEY: {'✅ Present' if SUPABASE_SERVICE_KEY else '❌ MISSING'}")

def validate_recaptcha(token, remote_ip=None):
    """Validate reCAPTCHA token with Google"""
    try:
        if not RECAPTCHA_SECRET_KEY:
            logger.warning("reCAPTCHA secret key not configured")
            return False, "reCAPTCHA not configured"

        logger.info(f"Validating reCAPTCHA token: {token[:20]}...")
        
        # Verify token with Google
        verification_url = 'https://www.google.com/recaptcha/api/siteverify'
        verification_data = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': token,
            'remoteip': remote_ip
        }

        logger.info("Sending verification request to Google...")
        response = requests.post(verification_url, data=verification_data, timeout=10)
        result = response.json()
        
        logger.info(f"Google reCAPTCHA response: {result}")

        # Check if verification was successful
        is_valid = result.get('success', False)
        score = result.get('score', 0)
        
        # For reCAPTCHA v3, check score threshold (0.5 is typically good)
        if is_valid and score >= 0.5:
            logger.info(f"reCAPTCHA validation successful with score: {score}")
            return True, None
        else:
            logger.warning(f"reCAPTCHA validation failed. Success: {is_valid}, Score: {score}")
            error_codes = result.get('error-codes', [])
            return False, f"reCAPTCHA validation failed. Errors: {error_codes}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during reCAPTCHA verification: {e}")
        return False, f"Network error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error during reCAPTCHA verification: {e}")
        return False, f"Verification error: {str(e)}"

@auth_routes.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        recaptcha_token = data.get("recaptcha")
        
        # Validate reCAPTCHA first
        if not recaptcha_token:
            logger.warning("No reCAPTCHA token provided for registration")
            return jsonify({"message": "reCAPTCHA token required"}), 400
            
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        if not is_valid:
            logger.warning(f"reCAPTCHA validation failed for registration: {error_message}")
            return jsonify({"message": "Invalid reCAPTCHA"}), 400

        email = data.get("email")
        password = data.get("password")
        username = data.get("username")

        if not all([email, password, username]):
            return jsonify({"message": "Missing required fields."}), 400

        # Register with Supabase
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": { "data": { "username": username } }
        })
        
        # Fix: Access attributes directly instead of using .get()
        if hasattr(result, 'error') and result.error:
            return jsonify({"message": result.error.message}), 400

        if not hasattr(result, 'data') or not result.data or not result.data.user:
            return jsonify({"message": "Registration failed"}), 400

        user = result.data.user

        # Create profile in Supabase
        profile_result = supabase.table("profiles").insert({
            "id": user.id,
            "email": email,
            "username": username,
            "name": username
        }).execute()

        if profile_result.data:
            return jsonify({"message": "User registered successfully!"}), 201
        else:
            return jsonify({"message": "Profile creation failed"}), 400
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"message": "Registration failed"}), 500

@auth_routes.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        logger.info(f"Login attempt for email: {data.get('email', 'N/A')}")
        
        recaptcha_token = data.get("recaptcha")
        
        # Validate reCAPTCHA first
        if not recaptcha_token:
            logger.warning("No reCAPTCHA token provided for login")
            return jsonify({"message": "reCAPTCHA token required"}), 400
            
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        if not is_valid:
            logger.warning(f"reCAPTCHA validation failed for login: {error_message}")
            return jsonify({"message": "Invalid reCAPTCHA"}), 400

        email = data.get("email")
        password = data.get("password")
        if not all([email, password]):
            logger.warning("Missing email or password")
            return jsonify({"message": "Missing email or password"}), 400

        # Authenticate with Supabase
        logger.info(f"Attempting Supabase authentication for: {email}")
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Debug: Log the full result structure
        logger.info(f"Supabase result type: {type(result)}")
        logger.info(f"Supabase result attributes: {dir(result)}")
        
        # Fix: Check for errors properly
        if hasattr(result, 'error') and result.error:
            logger.error(f"Supabase auth error: {result.error}")
            return jsonify({"message": str(result.error)}), 401

        # Fix: Access user data more defensively
        user = None
        if hasattr(result, 'data') and result.data:
            if hasattr(result.data, 'user') and result.data.user:
                user = result.data.user
            elif hasattr(result.data, 'get'):
                user = result.data.get('user')
        
        # Also try direct access in case it's a different structure
        if not user and hasattr(result, 'user'):
            user = result.user
            
        if not user:
            logger.error(f"No user data found in result. Result structure: {vars(result) if hasattr(result, '__dict__') else 'No __dict__'}")
            return jsonify({"message": "Authentication failed - no user data"}), 401

        user_id = user.id if hasattr(user, 'id') else user.get('id') if hasattr(user, 'get') else None
        user_email = user.email if hasattr(user, 'email') else user.get('email') if hasattr(user, 'get') else None
        
        if not user_id:
            logger.error("User ID not found in user object")
            return jsonify({"message": "Authentication failed - no user ID"}), 401
            
        logger.info(f"Supabase auth successful for user ID: {user_id}")

        # Get user profile
        profile_result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        
        if not profile_result.data:
            logger.error(f"No profile found for user ID: {user_id}")
            return jsonify({"message": "User profile not found"}), 404

        profile = profile_result.data
        logger.info(f"Profile found for user: {profile.get('username')}")
        
        # Create our own JWT token with user data
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                "email": user_email,
                "username": profile.get("username"),
                "name": profile.get("name"),
                "avatar_url": profile.get("avatar_url")
            }
        )

        logger.info(f"Login successful for user: {profile.get('username')}")
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user_id,
                "email": user_email,
                "username": profile.get("username"),
                "name": profile.get("name"),
                "avatar_url": profile.get("avatar_url")
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({"message": f"Login failed: {str(e)}"}), 500

@auth_routes.route('/verify-token', methods=['POST', 'OPTIONS'])
@jwt_required()
def verify_token():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        current_user_id = get_jwt_identity()
        # Get additional claims from the token
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        return jsonify({
            "valid": True,
            "user": {
                "id": current_user_id,
                "email": claims.get("email"),
                "username": claims.get("username"),
                "name": claims.get("name"),
                "avatar_url": claims.get("avatar_url")
            }
        }), 200
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({"message": "Invalid token", "error": str(e)}), 401

@auth_routes.route('/verify-recaptcha', methods=['POST', 'OPTIONS'])
def verify_recaptcha():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    if not validate_recaptcha(data.get("recaptcha")):
        return jsonify({"success": False, "message": "Invalid reCAPTCHA"}), 400
    return jsonify({"success": True}), 200

@auth_routes.route('/test-connection', methods=['GET', 'OPTIONS'])
def test_connection():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Test Supabase connection
        result = supabase.table("profiles").select("count", count="exact").execute()
        return jsonify({
            "supabase_connection": "OK",
            "profile_count": result.count if hasattr(result, 'count') else "unknown"
        }), 200
    except Exception as e:
        logger.error(f"Test connection error: {str(e)}")
        return jsonify({
            "supabase_connection": "FAILED",
            "error": str(e)
        }), 500
