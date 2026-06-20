"""
Flask-Masonite: A Masonite-inspired routing and controller engine for Flask applications
"""

from functools import wraps
from flask import request, jsonify, g
from .helpers import get_signature, resolve_dependency
import inspect


class ControllerMeta(type):
    """
    Metaclass for Controller that keeps track of all registered controllers.
    """
    controllers = []

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        
        # Don't register the base Controller class itself
        if name != 'Controller':
            cls.controllers.append(new_class)
            
        return new_class


class Controller(metaclass=ControllerMeta):
    """
    Base Controller class inspired by Masonite.
    
    Controllers are used to group related request handling logic. Each controller
    method represents a specific endpoint or action.
    
    Example:
    >>> from flask_masonite import Controller
    
    >>> class UserController(Controller):
    ...     def index(self):
    ...         return {'message': 'Hello World'}
    ...     
    ...     def show(self, id):
    ...         return {'id': id, 'name': f'User {id}'}
    """

    def __init__(self):
        self.middleware = []
        self.before_middleware = []
        self.after_middleware = []

    @classmethod
    def get_controllers(cls):
        """
        Get all registered controllers.
        """
        return ControllerMeta.controllers

    def dispatch(self, method_name, *args, **kwargs):
        """
        Dispatch a method call with dependency injection.
        """
        method = getattr(self, method_name)
        signature = inspect.signature(method)
        
        # Resolve dependencies based on annotations
        resolved_args = []
        for param in signature.parameters.values():
            if param.annotation != param.empty:
                resolved_arg = resolve_dependency(param.annotation)
                if resolved_arg is not None:
                    resolved_args.append(resolved_arg)
                elif param.default != param.empty:
                    resolved_args.append(param.default)
                else:
                    resolved_args.append(None)
            elif param.default != param.empty:
                resolved_args.append(param.default)
            else:
                resolved_args.append(None)
                
        return method(*resolved_args)


class Route:
    """
    Route class inspired by Masonite's routing system.
    
    Provides a fluent interface for defining routes with various HTTP methods.
    
    Example:
    >>> from flask_masonite import Route
    >>> routes = [
    ...     Route.get('/users', 'UserController@index'),
    ...     Route.post('/users', 'UserController@store'),
    ...     Route.resource('/posts', 'PostController')
    ... ]
    """
    
    def __init__(self, path, handler, methods=None, name=None):
        self.path = path
        self.handler = handler
        self.methods = methods or ['GET']
        self._before_middleware = []
        self._after_middleware = []
        self._conditional_middleware = []
        self.name = name  # Add name attribute
        
    @property
    def url(self):
        """Return the route's URL path"""
        return self.path

    @classmethod
    def get(cls, path, handler, name=None):
        """Create a GET route."""
        return cls(path, handler, ['GET'], name)

    @classmethod
    def post(cls, path, handler, name=None):
        """Create a POST route."""
        return cls(path, handler, ['POST'], name)

    @classmethod
    def put(cls, path, handler, name=None):
        """Create a PUT route."""
        return cls(path, handler, ['PUT'], name)

    @classmethod
    def patch(cls, path, handler, name=None):
        """Create a PATCH route."""
        return cls(path, handler, ['PATCH'], name)

    @classmethod
    def delete(cls, path, handler, name=None):
        """Create a DELETE route."""
        return cls(path, handler, ['DELETE'], name)

    @classmethod
    def any(cls, path, handler, name=None):
        """Create a route that accepts any HTTP method."""
        return cls(path, handler, ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], name)

    @classmethod
    def resource(cls, path, controller, name=None):
        """
        Create a resource route that automatically generates RESTful routes.
        
        Generates:
        - GET /resource -> controller.index
        - GET /resource/create -> controller.create
        - POST /resource -> controller.store
        - GET /resource/{id} -> controller.show
        - GET /resource/{id}/edit -> controller.edit
        - PUT/PATCH /resource/{id} -> controller.update
        - DELETE /resource/{id} -> controller.destroy
        """
        routes = []
        
        # Standard RESTful routes
        routes.append(cls(f"{path}", f"{controller}@index", ['GET'], f"{name}.index" if name else f"{controller.lower()}.index"))
        routes.append(cls(f"{path}/create", f"{controller}@create", ['GET'], f"{name}.create" if name else f"{controller.lower()}.create"))
        routes.append(cls(f"{path}", f"{controller}@store", ['POST'], f"{name}.store" if name else f"{controller.lower()}.store"))
        routes.append(cls(f"{path}/<int:id>", f"{controller}@show", ['GET'], f"{name}.show" if name else f"{controller.lower()}.show"))
        routes.append(cls(f"{path}/<int:id>/edit", f"{controller}@edit", ['GET'], f"{name}.edit" if name else f"{controller.lower()}.edit"))
        routes.append(cls(f"{path}/<int:id>", f"{controller}@update", ['PUT', 'PATCH'], f"{name}.update" if name else f"{controller.lower()}.update"))
        routes.append(cls(f"{path}/<int:id>", f"{controller}@destroy", ['DELETE'], f"{name}.destroy" if name else f"{controller.lower()}.destroy"))
        
        return routes

    @classmethod
    def group(cls, routes, prefix="", name_prefix=""):
        """
        Group multiple routes under a common prefix and/or name prefix.
        
        Args:
            routes: List of Route objects to group
            prefix: URL prefix to add to all routes
            name_prefix: Name prefix to add to all route names
        """
        grouped_routes = []
        for route in routes:
            # Create new route with prefixed path
            new_path = f"{prefix}{route.path}" if prefix else route.path
            new_name = f"{name_prefix}.{route.name}" if name_prefix and route.name else route.name
            new_route = cls(new_path, route.handler, route.methods, new_name)
            grouped_routes.append(new_route)
        return grouped_routes

    def middleware(self, middleware_class, **options):
        """
        Add middleware to this route.
        
        :param middleware_class: The middleware class to add
        :param options: Additional options like 'only' or 'except' for specific methods
        """
        self._conditional_middleware.append((middleware_class, options))
        return self

    def before(self, func):
        """Add a before middleware function."""
        self._before_middleware.append(func)
        return self

    def after(self, func):
        """Add an after middleware function."""
        self._after_middleware.append(func)
        return self

    def handle_request(self, app, *args, **kwargs):
        """
        Handle the incoming request by applying middleware and calling the handler.
        """
        # Apply before middleware
        for middleware_func in self._before_middleware:
            result = middleware_func(request)
            if result is not None:
                return result
        
        # Parse the handler (e.g. 'UserController@method')
        if '@' in self.handler:
            controller_name, method_name = self.handler.split('@', 1)
            controller_class = self._get_controller_by_name(controller_name)
            
            if controller_class:
                controller_instance = controller_class()
                
                # Apply controller-level middleware
                for middleware_item in controller_instance.middleware:
                    if isinstance(middleware_item, tuple):
                        middleware_cls, options = middleware_item
                        # Check if this middleware applies to the current method
                        if self._should_apply_middleware(options, method_name):
                            middleware_instance = middleware_cls()
                            result = middleware_instance.before()
                            if result is not None:
                                return result
                    else:
                        middleware_instance = middleware_item()
                        result = middleware_instance.before()
                        if result is not None:
                            return result
                
                # Call the controller method with dependency injection
                result = controller_instance.dispatch(method_name, *args, **kwargs)
                
                # Apply controller-level after middleware
                for middleware_item in reversed(controller_instance.middleware):
                    if isinstance(middleware_item, tuple):
                        middleware_cls, options = middleware_item
                        if self._should_apply_middleware(options, method_name):
                            middleware_instance = middleware_cls()
                            middleware_instance.after(result)
                    else:
                        middleware_instance = middleware_item()
                        middleware_instance.after(result)
                        
                return result
            else:
                return jsonify({'error': f'Controller {controller_name} not found'}), 404
        else:
            # If handler is a function, call it directly
            return self.handler(*args, **kwargs)

    def _should_apply_middleware(self, options, method_name):
        """Check if middleware should be applied based on only/except options."""
        if 'only' in options:
            return method_name in options['only']
        elif 'except' in options:
            return method_name not in options['except']
        return True

    def _get_controller_by_name(self, controller_name):
        """
        Retrieve controller class by name using dynamic import.
        """
        # Search in the registered controllers
        for controller_class in ControllerMeta.controllers:
            if controller_class.__name__ == controller_name:
                return controller_class
        return None


class RouteCollection:
    """
    Collection of routes that can be registered with a Flask app.
    """
    
    def __init__(self, routes=None):
        self.routes = routes or []
    
    def add(self, route):
        """Add a route to the collection."""
        self.routes.append(route)
        return self
    
    def extend(self, routes):
        """Extend the collection with multiple routes."""
        self.routes.extend(routes)
        return self
    
    def register(self, app):
        """Register all routes with the given Flask app."""
        for route in self.routes:
            # Create a Flask-compatible view function
            def make_view(route_ref=route):
                def view(*args, **kwargs):
                    return route_ref.handle_request(app, *args, **kwargs)
                return view
            
            view_func = make_view(route)
            
            # Register the route with Flask
            app.add_url_rule(
                rule=route.path,
                endpoint=route.name or f"{route.handler.replace('@', '_')}",
                view_func=view_func,
                methods=route.methods
            )
    
    def resource(self, path, controller):
        """Add a resource route to the collection."""
        resource_routes = Route.resource(path, controller)
        self.routes.extend(resource_routes)
        return self


class ResourceRoute(Route):
    """
    Specialized route class for resource-based routing.
    """
    pass


class Middleware:
    """
    Base Middleware class.
    
    Middlewares can intercept requests before they reach the controller
    and responses after the controller has processed them.
    
    Example:
    >>> class AuthMiddleware(Middleware):
    ...     def before(self):
    ...         # Code to run before the request reaches the controller
    ...         if not request.headers.get('Authorization'):
    ...             return jsonify({'error': 'Unauthorized'}), 401
    ...
    ...     def after(self, response):
    ...         # Code to run after the controller has processed the request
    ...         # e.g., add headers to the response
    ...         response.headers['X-Powered-By'] = 'Flask-Masonite'
    ...         return response
    """
    
    def before(self):
        """
        Run code before the request reaches the controller.
        Return a response to short-circuit the request.
        """
        pass
    
    def after(self, response):
        """
        Run code after the controller has processed the request.
        Can modify the response before it's sent to the client.
        """
        return response


def register_controllers_from_paths(app, controller_paths):
    """
    Register controllers from specified module paths.
    
    Args:
        app: Flask application instance
        controller_paths: List of module paths to import controllers from
    """
    import importlib
    
    for path in controller_paths:
        try:
            importlib.import_module(path)
        except ImportError as e:
            print(f"Could not import controller module {path}: {e}")