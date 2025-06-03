### MONKEY PATCHING ###
from gevent import monkey
monkey.patch_all()
### END MONKEY PATCHING ###

import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from api.bots import bot_routes
from api.auth import auth_routes
from api.online import online_routes
from socketio_instance import socketio


### CONFIGURATION ###
# Load environment variables
load_dotenv()

# Verify critical env vars are loaded
recaptcha_key = os.getenv('RECAPTCHA_SECRET_KEY')
jwt_key = os.getenv('JWT_SECRET_KEY')

print(f"Environment loaded - RECAPTCHA_SECRET_KEY: {'✅ Present' if recaptcha_key else '❌ MISSING'}")
print(f"Environment loaded - JWT_SECRET_KEY: {'✅ Present' if jwt_key else '❌ MISSING'}")

class Config:
    """Base configuration."""
    DEBUG = os.getenv("DEBUG", True)
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = os.getenv("PORT", 5000)

app = Flask(__name__)
app.config.from_object(Config)  
app.config['JWT_SECRET_KEY'] = jwt_key
### END CONFIGURATION ###


### CORS ###
allowed_origins = [
    "http://localhost:3000",
    "https://www.utictactoe.online",
    "https://utictactoe.online",
    "https://utictactoe.vercel.app"
]

CORS(app, 
     resources={r"/*": {
         "origins": allowed_origins,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
         "supports_credentials": True,
         "max_age": 86400  # Cache preflight response for 24 hours
     }}
)

@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = app.make_default_options_response()
    headers = response.headers

    headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    headers['Access-Control-Allow-Credentials'] = 'true'
    headers['Access-Control-Max-Age'] = '86400'

    return response


@app.after_request
def after_request(response):
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    headers['Access-Control-Allow-Credentials'] = 'true'
    headers['Access-Control-Max-Age'] = '86400'
    return response
### END CORS ###


### JWT ###
jwt = JWTManager(app)

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"message": "Missing or invalid token."}), 401

@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired."}), 401
### END JWT ###


### ROUTES ###
app.register_blueprint(bot_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(online_routes)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status="healthy"), 200
#### END ROUTES ###


### SOCKET.IO ###
socketio.init_app(app, cors_allowed_origins="*")
### END SOCKET.IO ###


### STARTUP LOGIC ###
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False)
### END STARTUP LOGIC ###
