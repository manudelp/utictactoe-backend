import os
import requests

def validate_recaptcha(token, remote_ip=None):
    """Validate reCAPTCHA token with Google"""
    try:
        secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        
        if not secret_key:
            print("reCAPTCHA secret key not configured")
            return False, "reCAPTCHA not configured"

        print(f"Validating reCAPTCHA token: {token[:20]}...")
        
        # Verify token with Google
        verification_url = 'https://www.google.com/recaptcha/api/siteverify'
        verification_data = {
            'secret': secret_key,
            'response': token,
            'remoteip': remote_ip
        }

        print("Sending verification request to Google...")
        response = requests.post(verification_url, data=verification_data, timeout=10)
        result = response.json()
        
        print(f"Google reCAPTCHA response: {result}")

        # Check if verification was successful
        is_valid = result.get('success', False)
        score = result.get('score', 0)
        
        # For reCAPTCHA v3, check score threshold (0.5 is typically good)
        if is_valid and score >= 0.5:
            print(f"reCAPTCHA validation successful with score: {score}")
            return True, None
        else:
            print(f"reCAPTCHA validation failed. Success: {is_valid}, Score: {score}")
            error_codes = result.get('error-codes', [])
            return False, f"reCAPTCHA validation failed. Errors: {error_codes}"

    except requests.exceptions.RequestException as e:
        print(f"Network error during reCAPTCHA verification: {e}")
        return False, f"Network error: {str(e)}"
    
    except Exception as e:
        print(f"Error during reCAPTCHA verification: {e}")
        return False, f"Verification error: {str(e)}"
