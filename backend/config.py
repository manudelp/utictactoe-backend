# backend/config.py

import os

class Config:
    """Base configuration."""
    DEBUG = os.getenv("DEBUG", True)  # Set to False in production
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = os.getenv("PORT", 5000)