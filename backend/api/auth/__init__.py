from flask import Blueprint
import os

# Create the auth blueprint
auth_routes = Blueprint('auth', __name__)

# Import routes at the end to avoid circular imports
from . import routes
