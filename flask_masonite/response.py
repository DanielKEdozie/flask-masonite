from flask import jsonify, render_template, redirect, make_response

class Response:
    """
    A Response builder wrapper for Flask.
    Provides a fluent interface to construct and return HTTP responses.
    """
    def __init__(self):
        self._status = 200
        self._headers = {}

    def status(self, code):
        """Set HTTP status code fluently"""
        self._status = code
        return self

    def header(self, name, value):
        """Set an HTTP response header fluently"""
        self._headers[name] = value
        return self

    def json(self, data, status=None):
        """Return a JSON response"""
        status_code = status or self._status
        resp = jsonify(data)
        resp.status_code = status_code
        for k, v in self._headers.items():
            resp.headers[k] = v
        # Reset builder state
        self._status = 200
        self._headers = {}
        return resp

    def template(self, template_name, status=None, **context):
        """Alias for view method"""
        return self.view(template_name, status=status, **context)

    def view(self, template_name, status=None, **context):
        """Render a template response"""
        status_code = status or self._status
        html = render_template(template_name, **context)
        resp = make_response(html, status_code)
        for k, v in self._headers.items():
            resp.headers[k] = v
        # Reset builder state
        self._status = 200
        self._headers = {}
        return resp

    def redirect(self, location, status=302):
        """Redirect response"""
        resp = redirect(location, code=status)
        for k, v in self._headers.items():
            resp.headers[k] = v
        # Reset builder state
        self._status = 200
        self._headers = {}
        return resp
