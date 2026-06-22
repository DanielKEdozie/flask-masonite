import inspect
from flask import request as flask_request

class Request:
    """
    A Masonite-like request wrapper for Flask.
    Provides a cleaner, more intuitive API for accessing request data.
    """
    def __getattr__(self, name):
        # Proxy attributes directly to the underlying flask request
        return getattr(flask_request, name)

    @property
    def params(self):
        """Get query string parameters as a dictionary"""
        return flask_request.args.to_dict()

    @property
    def url_params(self):
        """Get URL route parameters (view args) as a dictionary"""
        return flask_request.view_args or {}

    def param(self, key, default=None):
        """Get a specific URL route parameter"""
        return (flask_request.view_args or {}).get(key, default)

    def input(self, key, default=None):
        """Get input data from JSON, POST form, or query parameters (in that order)"""
        if flask_request.is_json:
            json_data = flask_request.get_json(silent=True) or {}
            if key in json_data:
                return json_data[key]
        
        if key in flask_request.form:
            values = flask_request.form.getlist(key)
            return values if len(values) > 1 else values[0]
            
        if key in flask_request.args:
            values = flask_request.args.getlist(key)
            return values if len(values) > 1 else values[0]
            
        return default

    def query(self, key, default=None):
        """Strictly retrieve a query string parameter"""
        if key in flask_request.args:
            values = flask_request.args.getlist(key)
            return values if len(values) > 1 else values[0]
        return default

    def all(self, type=None):
        """
        Get request inputs.
        If type is specified ('json', 'form', 'query'), returns only inputs from that source.
        Otherwise, returns a combined dictionary of all inputs.
        """
        if type == 'json':
            if flask_request.is_json:
                return flask_request.get_json(silent=True) or {}
            return {}
        elif type == 'form':
            return flask_request.form.to_dict()
        elif type == 'query':
            return flask_request.args.to_dict()
            
        data = {}
        # 1. Query parameters
        data.update(flask_request.args.to_dict())
        # 2. Form data
        data.update(flask_request.form.to_dict())
        # 3. JSON data
        if flask_request.is_json:
            data.update(flask_request.get_json(silent=True) or {})
        return data

    def has(self, key):
        """Check if request has input key"""
        return key in self.all()

    def user(self):
        """Get the current authenticated user if Flask-Login/Flask-User is active"""
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                return current_user
        except ImportError:
            pass
        return None
