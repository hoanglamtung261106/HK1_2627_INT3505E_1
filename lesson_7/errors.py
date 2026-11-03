# src/product_api/errors.py
from flask import jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

class ApiError(Exception):
    status_code = 500
    code = "internal_error"
    def __init__(self, message="", code=None, status=None):
        super().__init__(message)
        self.message = message
        if code: self.code = code
        if status: self.status_code = status

class NotFound(ApiError):
    status_code = 404
    code = "not_found"

class Conflict(ApiError):
    status_code = 409
    code = "conflict"

def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify({"code": err.code, "message": err.message}), err.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"code": "validation_error", "message": err.messages}), 422

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({
            "code": err.name.lower().replace(" ", "_"),
            "message": err.description
        }), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        app.logger.exception("Unhandled Exception")
        return jsonify({"code": "internal_error", "message": "An unexpected error occurred"}), 500