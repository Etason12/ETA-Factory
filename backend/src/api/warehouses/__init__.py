from flask import Blueprint

warehouses_bp = Blueprint('warehouses', __name__)

from . import routes
