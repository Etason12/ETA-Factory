from flask import Blueprint

raw_materials_bp = Blueprint('raw_materials', __name__)

from . import routes
