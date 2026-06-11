from flask import Blueprint

transfers_bp = Blueprint('transfers', __name__)

from . import routes
