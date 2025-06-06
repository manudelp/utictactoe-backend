import os
import requests
from flask import Blueprint, request, jsonify
from recaptcha_utils import validate_recaptcha

# Create blueprint for test endpoints
test_bp = Blueprint('test', __name__)

@test_bp.route('/test-recaptcha', methods=['POST'])
def test_recaptcha():
    """Test endpoint to validate reCAPTCHA tokens"""
    try:
        data = request.get_json()
        
        if not data or 'recaptcha' not in data:
            return jsonify({
                'valid': False, 
                'error': 'No reCAPTCHA token provided'
            }), 400

        recaptcha_token = data['recaptcha']

        # Validate reCAPTCHA
        is_valid, error_message = validate_recaptcha(recaptcha_token, request.remote_addr)
        
        if is_valid:
            return jsonify({
                'valid': True,
                'score': 0.9,  # Mock score for successful validation
                'action': 'test',
                'debug_info': {
                    'token_length': len(recaptcha_token),
                    'secret_key_length': 40,  # Mock length
                    'remote_ip': request.remote_addr
                }
            })
        else:
            return jsonify({
                'valid': False,
                'error': error_message
            }), 400

    except Exception as e:
        print(f"Error during reCAPTCHA test: {e}")
        return jsonify({
            'valid': False,
            'error': f'Test error: {str(e)}'
        }), 500
