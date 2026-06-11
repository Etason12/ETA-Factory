from flask import Blueprint

branches_bp = Blueprint('branches', __name__)

from . import routes
