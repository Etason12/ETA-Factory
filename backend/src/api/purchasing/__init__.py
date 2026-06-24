from flask import Blueprint

purchasing_bp = Blueprint('purchasing', __name__)

from . import routes
