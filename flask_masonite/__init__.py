from .masonite import Controller, Route, RouteCollection, RouteGroup, ResourceRoute, Middleware, register_controllers_from_paths
from .routing import Router, route, get, post, put, delete, patch
from .middleware import wrap_with_middleware, AuthMiddleware, APIAuthMiddleware
from .helpers import get_signature, resolve_dependency
from .helpers_classes import Task, Email, Security
from .extensions import register_extension, get_extension, initialize_extension, extension_manager

__all__ = [
    'Controller',
    'Route',
    'RouteCollection',
    'RouteGroup',
    'ResourceRoute',
    'Middleware',
    'Router',
    'route',
    'get',
    'post',
    'put', 
    'delete',
    'patch',
    'wrap_with_middleware',
    'get_signature',
    'resolve_dependency',
    'register_controllers_from_paths',
    'register_extension',
    'get_extension',
    'initialize_extension',
    'extension_manager',
    'AuthMiddleware',
    'APIAuthMiddleware',
    'Task',
    'Email',
    'Security',
    'FlaskMasonite'
]

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "edozie857@gmail.com"


class FlaskMasonite:
    """
    Unified Flask-Masonite framework class that encapsulates all functionality
    and provides a clean init_app method for Flask application initialization.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the Flask application with Flask-Masonite functionality.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Initialize extensions with app
        initialize_extension(app)
        
        # Register controllers from paths defined in app config
        controller_paths = app.config.get('CONTROLLER_PATHS', [])
        register_controllers_from_paths(app, controller_paths)
        
        # Store reference to the framework in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        if 'flask_masonite' in app.extensions:
            raise RuntimeError("Flask application already initialized")
        app.extensions['flask_masonite'] = self
        
        # Add a method to register routes
        app.register_routes = self._register_routes
        
        # Override url_for to support resolving dot-containing endpoints with underscores
        import flask
        import flask.helpers
        
        if not hasattr(flask, '_original_url_for'):
            flask._original_url_for = flask.url_for
            
            def custom_url_for(endpoint, **values):
                try:
                    return flask._original_url_for(endpoint, **values)
                except Exception as e:
                    if '.' in endpoint:
                        # Translate hierarchical dot-containing endpoints to matching normalized blueprint names
                        # e.g., api.v1.user.index -> api_v1_user.index
                        parts = endpoint.rsplit('.', 1)
                        alt_endpoint = f"{parts[0].replace('.', '_')}.{parts[1]}"
                        try:
                            return flask._original_url_for(alt_endpoint, **values)
                        except Exception:
                            # Fallback: replacing all dots with underscores just in case
                            alt_endpoint2 = endpoint.replace('.', '_')
                            try:
                                return flask._original_url_for(alt_endpoint2, **values)
                            except Exception:
                                pass
                    raise e
                    
            flask.url_for = custom_url_for
            flask.helpers.url_for = custom_url_for
    
    def _register_routes(self, routes):
        """
        Register routes with the Flask application.
        
        Args:
            routes: RouteCollection or list of routes to register
        """
        if isinstance(routes, list):
            routes = RouteCollection(routes)
        routes.register(self.app)
        return routes
    
    def get_controllers(self):
        """Get all registered controllers."""
        return Controller.get_controllers()
    
    def create_resource_routes(self, path, controller):
        """Create resource routes for a controller."""
        return Route.resource(path, controller)