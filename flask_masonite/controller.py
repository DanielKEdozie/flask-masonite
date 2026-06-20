from flask import request, abort
from inspect import signature
import inspect
from .helpers import resolve_dependency, get_signature
from .middleware import wrap_with_middleware

class Controller:
    """
    Base Controller class for building class-based views.
    Any subclass of this will automatically be registered in Controller._registry.
    """
    _registry = {}
    _bindings = {}

    def __init__(self):
        self.request = request

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register the class name in various formats (case-insensitive)
        name = cls.__name__
        cls._registry[name] = cls
        cls._registry[name.lower()] = cls
        
        # Also register with typical suffixes removed (e.g. VendorController -> vendor)
        name_lower = name.lower()
        for suffix in ('controller', 'route', 'view'):
            if name_lower.endswith(suffix) and name_lower != suffix:
                cls._registry[name_lower[:-len(suffix)]] = cls
                break

    @classmethod
    def bind(cls, key, resolver):
        """
        Registers a dependency injection binding.
        key: class type or string name.
        resolver: a class instance, factory function (callable), or a class.
        """
        cls._bindings[key] = resolver

    @classmethod
    def as_view(cls, action, name=None):
        """
        Creates a Flask-compatible view function that instantiates the controller
        and executes the specified action (method).
        """
        def view(*args, **kwargs):
            # Resolve parameters for __init__ using Dependency Injection
            init_sig = signature(cls.__init__)
            init_kwargs = {}
            for param_name, param in init_sig.parameters.items():
                if param_name in ('self', 'args', 'kwargs'):
                    continue
                
                annotation = param.annotation
                val = resolve_dependency(annotation, param_name)
                if val is not None:
                    init_kwargs[param_name] = val
            
            instance = cls(**init_kwargs)
            instance.request = request
            
            # Execute action
            if not hasattr(instance, action):
                abort(404, description=f"Action '{action}' not found on controller '{cls.__name__}'")
            
            handler_func = getattr(instance, action)
            sig = get_signature(handler_func)
            
            # Resolve parameters using Dependency Injection
            resolved_kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                annotation = param.annotation
                val = resolve_dependency(annotation, param_name, kwargs)
                if val is not None:
                    resolved_kwargs[param_name] = val
                elif param_name in kwargs:
                    resolved_kwargs[param_name] = kwargs[param_name]
            
            # Hook before_filter: runs before executing the action
            if hasattr(instance, 'before_filter'):
                response = instance.before_filter(action, *args, **kwargs)
                if response is not None:
                    return response
            
            # Call handler with resolved arguments
            response = handler_func(*args, **resolved_kwargs)
            
            # Hook after_filter: runs after executing the action, allowing response modification
            if hasattr(instance, 'after_filter'):
                response = instance.after_filter(action, response)
                
            return response
            
        # Set view.__name__ so Flask can register the endpoint properly (dots are replaced with underscores)
        view_name = name or f"{cls.__name__.lower()}_{action}"
        view.__name__ = view_name.replace('.', '_')

        # Apply class-level middleware if defined
        if hasattr(cls, 'middleware') and cls.middleware:
            view = wrap_with_middleware(view, cls.middleware, action=action)

        # Apply class-level decorators (like Flask MethodView decorators attribute)
        if hasattr(cls, 'decorators') and cls.decorators:
            for decorator in cls.decorators:
                view = decorator(view)

        return view