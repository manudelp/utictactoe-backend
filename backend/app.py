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
from database import test_connection, init_database


### DATABASE SETUP ###
test_connection()
init_database()
### END DATABASE SETUP ###

### CONFIGURATION ###
load_dotenv()
class Config:
    """Base configuration."""
    DEBUG = os.getenv("DEBUG", True)
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = os.getenv("PORT", 5000)

app = Flask(__name__)
app.config.from_object(Config)  
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
### END CONFIGURATION ###


### CORS ###
def get_cors_origin():
    origin = request.headers.get('Origin')
    allowed_origins = [
        "http://localhost:3000",
        "https://www.utictactoe.online",
        "https://utictactoe.online",
        "https://utictactoe.vercel.app"
    ]
    if origin in allowed_origins:
        return origin
    return None

CORS(app, resources={r"/*": {"origins": get_cors_origin}})
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


### ERROR HANDLERS ###
@app.errorhandler(Exception)
def handle_exception(e):
    response = {
        "message": "An unexpected error occurred.",
        "details": str(e)
    }
    return jsonify(response), 500
#### END ERROR HANDLERS ###


### SOCKET.IO ###
socketio.init_app(app, cors_allowed_origins="*")
### END SOCKET.IO ###


### STARTUP LOGIC ###
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False)
### END STARTUP LOGIC ###
