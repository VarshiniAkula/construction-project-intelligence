"""Vercel Serverless Function entry point for FastAPI."""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
