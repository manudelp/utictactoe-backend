import os
import requests
import jwt
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from supabase import create_client
from dotenv import load_dotenv
from . import auth_routes
from recaptcha_utils import validate_recaptcha

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@auth_routes.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        recaptcha_token = data.get("recaptcha")
        
        # Validate reCAPTCHA first
        if not recaptcha_token:
            return jsonify({"message": "reCAPTCHA token required"}), 400
            
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        if not is_valid:
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
        })
        
        user = None
        
        if hasattr(result, 'data'):
            if isinstance(result.data, dict):
                user = result.data.get('user')
            elif hasattr(result.data, 'user'):
                user = result.data.user

        if not user and hasattr(result, 'user'):
            user = result.user

        if not user:
            return jsonify({"message": "Registration failed"}), 400

        # Create profile in Supabase
        try:
            profile_result = supabase.table("profiles").insert({
                "id": user.id,
                "email": email,
                "username": username
            }).execute()
        except Exception as e:
            return jsonify({"message": "Failed to create user profile."}), 500

        if not profile_result.data:
            return jsonify({"message": "Profile creation failed"}), 400

        return jsonify({"message": "User registered successfully!"}), 201
            
    except Exception as e:
        return jsonify({"message": "Registration failed due to an internal error."}), 500

@auth_routes.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json       
        recaptcha_token = data.get("recaptcha")
        
        # Validate reCAPTCHA first
        if not recaptcha_token:
            return jsonify({"message": "reCAPTCHA token required"}), 400
            
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        if not is_valid:
            return jsonify({"message": "Invalid reCAPTCHA"}), 400

        email = data.get("email")
        password = data.get("password")
        if not all([email, password]):
            return jsonify({"message": "Missing email or password"}), 400

        # Authenticate with Supabase
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Check for errors properly
        if hasattr(result, 'error') and result.error:
            return jsonify({"message": str(result.error)}), 401

        # Access user data more defensively
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
            return jsonify({"message": "Authentication failed - no user data"}), 401

        user_id = user.id if hasattr(user, 'id') else user.get('id') if hasattr(user, 'get') else None
        user_email = user.email if hasattr(user, 'email') else user.get('email') if hasattr(user, 'get') else None
        
        if not user_id:
            return jsonify({"message": "Authentication failed - no user ID"}), 401

        # Get user profile
        profile_result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        
        if not profile_result.data:
            return jsonify({"message": "User profile not found"}), 404

        profile = profile_result.data
        
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
        return jsonify({"message": "Invalid token", "error": str(e)}), 401

@auth_routes.route('/verify-recaptcha', methods=['POST', 'OPTIONS'])
def verify_recaptcha():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json
    is_valid, error_message = validate_recaptcha(data.get("recaptcha"), request.remote_addr)
    if not is_valid:
        return jsonify({"success": False, "message": error_message}), 400
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
        return jsonify({
            "supabase_connection": "FAILED",
            "error": str(e)
        }), 500

@auth_routes.route('/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        recaptcha_token = data.get("recaptcha")
        
        # Validate reCAPTCHA first
        if not recaptcha_token:
            return jsonify({"message": "reCAPTCHA token required"}), 400
            
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        if not is_valid:
            return jsonify({"message": "Invalid reCAPTCHA"}), 400

        email = data.get("email")
        if not email:
            return jsonify({"message": "Email is required"}), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"message": "Invalid email format"}), 400

        # Get the frontend URL for the reset link - handle different environments
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        
        # Determine base URL with fallback logic
        if origin:
            base_url = origin
        elif referer:
            # Extract base URL from referer
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            # Default fallbacks for different environments
            base_url = 'https://utictactoe.vercel.app'  # Production default
        
        try:
            # Send password reset email via Supabase
            result = supabase.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": f"{base_url}/reset-password"
                }
            )
            
            # Check if there was an error in the result
            if hasattr(result, 'error') and result.error:
                # Don't reveal if email exists or not for security
                return jsonify({"message": "If an account with that email exists, a password reset link has been sent"}), 200
            
        except Exception as supabase_error:
            # Don't reveal if email exists or not for security
            return jsonify({"message": "If an account with that email exists, a password reset link has been sent"}), 200

        # Always return success message for security (don't reveal if email exists)
        return jsonify({"message": "If an account with that email exists, a password reset link has been sent"}), 200
        
    except Exception as e:
        return jsonify({"message": "Unable to process password reset request. Please try again later."}), 500

@auth_routes.route('/supabase-exchange', methods=['POST', 'OPTIONS'])
def supabase_exchange():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json
        supabase_token = data.get("supabase_token")
        user_data = data.get("user_data")
        
        if not supabase_token or not user_data:
            return jsonify({"message": "Missing required data"}), 400

        # Verify the Supabase token by getting user info
        try:
            import jwt
            # Decode without verification first to get the user ID
            decoded = jwt.decode(supabase_token, options={"verify_signature": False})
            user_id = decoded.get('sub')
            
            if not user_id or user_id != user_data.get('id'):
                return jsonify({"message": "Invalid token"}), 401
                
        except Exception as e:
            return jsonify({"message": "Invalid token format"}), 401

        # Get the most up-to-date profile data from database
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
            
            if profile_result.data and not profile_result.data.get('linked_to'):
                # Use database profile data as the source of truth
                db_profile = profile_result.data
                token_user_data = {
                    "id": user_id,
                    "email": db_profile.get('email', user_data.get('email')),
                    "username": db_profile.get('username', user_data.get('username')),
                    "name": db_profile.get('name', user_data.get('name')),
                    "avatar_url": db_profile.get('avatar_url', user_data.get('avatar_url')),
                    "provider": db_profile.get('provider', user_data.get('provider', 'email'))
                }
            else:
                # Create or update profile with provided data
                token_user_data = {
                    "id": user_data.get('id'),
                    "email": user_data.get('email'),
                    "username": user_data.get('username'),
                    "name": user_data.get('name'),
                    "avatar_url": user_data.get('avatar_url'),
                    "provider": user_data.get('provider', 'email')
                }
                
                # Upsert the profile
                supabase.table("profiles").upsert(token_user_data).execute()
                
        except Exception as e:
            # Fall back to provided user data
            token_user_data = {
                "id": user_data.get('id'),
                "email": user_data.get('email'),
                "username": user_data.get('username'),
                "name": user_data.get('name'),
                "avatar_url": user_data.get('avatar_url'),
                "provider": user_data.get('provider', 'email')
            }

        # Create our own JWT token with the finalized user data
        access_token = create_access_token(
            identity=token_user_data.get('id'),
            additional_claims={
                "email": token_user_data.get('email'),
                "username": token_user_data.get('username'),
                "name": token_user_data.get('name'),
                "avatar_url": token_user_data.get('avatar_url')
            }
        )

        return jsonify({
            "access_token": access_token,
            "user": token_user_data
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Token exchange failed: {str(e)}"}), 500
