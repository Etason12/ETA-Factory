import os
import sys
from flask import Flask, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from config.config import config_by_name
from models.models import db
from utils.error_handlers import register_error_handlers


class CORSMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD') == 'OPTIONS':
            start_response(
                '200 OK',
                [
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Headers', 'Content-Type,Authorization'),
                    ('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS'),
                    ('Content-Length', '0'),
                ]
            )
            return [b'']
        def cors_start_response(status, headers, exc_info=None):
            headers.append(('Access-Control-Allow-Origin', '*'))
            headers.append(('Access-Control-Allow-Headers', 'Content-Type,Authorization'))
            headers.append(('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS'))
            return start_response(status, headers, exc_info)
        return self.app(environ, cors_start_response)


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    app.wsgi_app = CORSMiddleware(app.wsgi_app)

    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    os.makedirs(os.path.join(uploads_dir, 'receipts'), exist_ok=True)
    app.config['UPLOADS_DIR'] = uploads_dir

    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(uploads_dir, filename)

    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        app.logger.warning('Expired token attempt')
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.warning('Invalid token attempt: %s', error)
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        app.logger.warning('Missing authorization header')
        return jsonify({'error': 'Missing authorization header'}), 401

    register_error_handlers(app)

    _register_blueprints(app)

    with app.app_context():
        from models import models as _models
        db.create_all()

    return app


def _register_blueprints(app: Flask) -> None:
    from api.auth.routes import auth_bp
    from api.users.routes import users_bp
    from api.branches.routes import branches_bp
    from api.products.routes import products_bp
    from api.customers.routes import customers_bp
    from api.inventory.routes import inventory_bp
    from api.warehouses.routes import warehouses_bp
    from api.production.routes import production_bp
    from api.sales.routes import sales_bp
    from api.transfers.routes import transfers_bp
    from api.reports.routes import reports_bp
    from api.audit.routes import audit_bp
    from api.company.routes import company_bp
    from api.roles.routes import roles_bp
    from api.raw_materials.routes import raw_materials_bp
    from api.suppliers.routes import suppliers_bp
    from api.purchasing.routes import purchasing_bp
    from api.store.routes import store_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(branches_bp, url_prefix='/api/v1/branches')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(customers_bp, url_prefix='/api/v1/customers')
    app.register_blueprint(inventory_bp, url_prefix='/api/v1/inventory')
    app.register_blueprint(warehouses_bp, url_prefix='/api/v1/warehouses')
    app.register_blueprint(production_bp, url_prefix='/api/v1/production')
    app.register_blueprint(sales_bp, url_prefix='/api/v1/sales')
    app.register_blueprint(transfers_bp, url_prefix='/api/v1/transfers')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(audit_bp, url_prefix='/api/v1/audit')
    app.register_blueprint(company_bp, url_prefix='/api/v1/company')
    app.register_blueprint(roles_bp, url_prefix='/api/v1/roles')
    app.register_blueprint(raw_materials_bp, url_prefix='/api/v1/raw-materials')
    app.register_blueprint(suppliers_bp, url_prefix='/api/v1/suppliers')
    app.register_blueprint(purchasing_bp, url_prefix='/api/v1/purchasing')
    app.register_blueprint(store_bp, url_prefix='/api/v1/store')

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
