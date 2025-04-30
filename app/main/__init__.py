# app/main/__init__.py
from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes
