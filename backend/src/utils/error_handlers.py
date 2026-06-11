import traceback
from flask import jsonify


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, message: str = 'Resource not found'):
        super().__init__(message, 404)


class ValidationError(AppError):
    def __init__(self, message: str = 'Validation error'):
        super().__init__(message, 400)


class UnauthorizedError(AppError):
    def __init__(self, message: str = 'Unauthorized'):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = 'Forbidden'):
        super().__init__(message, 403)


class ConflictError(AppError):
    def __init__(self, message: str = 'Conflict'):
        super().__init__(message, 409)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        if error.status_code >= 500:
            app.logger.error('AppError %d: %s', error.status_code, error.message)
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({'error': 'Unprocessable entity'}), 422

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('Internal server error: %s', traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
