from flask import request, abort
from functools import wraps
from typing import Callable, Dict, List, Optional, Union
import re

class Router:
    """Core routing system for Flask-Sonite framework"""
    
    def __init__(self):
        self.routes = []  # List of (pattern, view_func, methods, name)
        self.prefix = ''
        self.middleware = []
        
    def _compile_rule(self, rule: str) -> re.Pattern:
        """Convert URL rule to regex pattern, handling <param> placeholders"""
        # Convert <param> to named regex groups
        pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', rule)
        return re.compile(f'^{pattern}$')
        
    def route(self, rule: str, methods: List[str] = None, name: str = None):
        """Decorator to register a route"""
        if methods is None:
            methods = ['GET']
            
        def decorator(view_func: Callable):
            # Apply prefix if set
            full_rule = f"{self.prefix}{rule}"
            
            # Store route info
            self.routes.append((
                self._compile_rule(full_rule),
                view_func,
                [m.upper() for m in methods],
                name
            ))
            
            return view_func
        return decorator
    
    def _register(self, rule: str, handler, methods: List[str], name: str = None):
        """Direct route registration"""
        full_rule = f"{self.prefix}{rule}"
        self.routes.append((
            self._compile_rule(full_rule),
            handler,
            [m.upper() for m in methods],
            name
        ))
        return handler
    
    def get(self, rule: str, handler=None, name: str = None):
        """Shortcut for GET route - supports decorator and direct registration"""
        if handler is not None:
            return self._register(rule, handler, ['GET'], name)
        return self.route(rule, methods=['GET'], name=name)
        
    def post(self, rule: str, handler=None, name: str = None):
        """Shortcut for POST route"""
        if handler is not None:
            return self._register(rule, handler, ['POST'], name)
        return self.route(rule, methods=['POST'], name=name)
        
    def put(self, rule: str, handler=None, name: str = None):
        """Shortcut for PUT route"""
        if handler is not None:
            return self._register(rule, handler, ['PUT'], name)
        return self.route(rule, methods=['PUT'], name=name)
        
    def delete(self, rule: str, handler=None, name: str = None):
        """Shortcut for DELETE route"""
        if handler is not None:
            return self._register(rule, handler, ['DELETE'], name)
        return self.route(rule, methods=['DELETE'], name=name)
        
    def patch(self, rule: str, handler=None, name: str = None):
        """Shortcut for PATCH route"""
        if handler is not None:
            return self._register(rule, handler, ['PATCH'], name)
        return self.route(rule, methods=['PATCH'], name=name)
    
    def resources(self, resource: str, controller: str):
        """Generate RESTful routes for a resource"""
        self.get(f"/{resource}", f"{controller}.index", f"{resource}.index")
        self.get(f"/{resource}/<id>", f"{controller}.show", f"{resource}.show")
        self.post(f"/{resource}", f"{controller}.store", f"{resource}.store")
        self.put(f"/{resource}/<id>", f"{controller}.update", f"{resource}.update")
        self.patch(f"/{resource}/<id>", f"{controller}.update", f"{resource}.update")
        self.delete(f"/{resource}/<id>", f"{controller}.destroy", f"{resource}.destroy")
    
    def group(self, prefix: str, middleware: List = None):
        """Create a route group with common prefix and middleware"""
        if middleware is None:
            middleware = []
            
        # Create a sub-router that shares the parent's route list
        sub_router = Router()
        sub_router.prefix = f"{self.prefix}{prefix}"
        sub_router.middleware = self.middleware + middleware
        sub_router.routes = self.routes  # Share the same route list
        
        return sub_router
    
    def dispatch(self, request):
        """Dispatch request to matching route"""
        path = request.path
        method = request.method
        
        for pattern, view_func, methods, _ in self.routes:
            match = pattern.fullmatch(path)
            if match and method in methods:
                # Resolve string handler to controller method if needed
                handler = view_func
                if isinstance(handler, str):
                    if '.' in handler:
                        controller_name, action = handler.split('.')
                        from .masonite import Controller
                        cls = Controller._registry.get(controller_name.lower())
                        if not cls:
                            raise ValueError(f"Controller '{controller_name}' not found")
                        handler = cls.as_view(action)
                
                # Apply middleware if any
                wrapped_view = handler
                for mw in self.middleware:
                    wrapped_view = mw(wrapped_view)
                    
                # Extract URL parameters
                kwargs = match.groupdict()
                return wrapped_view(**kwargs)
                
        abort(404, description=f"Route {path} not found")

# Default router instance
router = Router()

# Shortcut decorators
route = router.route
get = router.get
post = router.post
put = router.put
delete = router.delete
patch = router.patch
