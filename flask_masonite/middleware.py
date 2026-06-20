import importlib
from typing import Any, Callable, List, Tuple, Union
from flask import request, make_response


def wrap_with_middleware(
    view_func: Callable,
    middleware: List[Union[Tuple[Any, dict], Any]],
    action: str = None
) -> Callable:
    """Wraps a view function with middleware layers.
    
    Args:
        view_func: The view function to wrap
        middleware: List of middleware classes or (class, options) tuples
        action: Optional action name for middleware filtering
    """
    for mw_item in reversed(middleware):
        # Unpack middleware item (can be just class or (class, options))
        if isinstance(mw_item, (tuple, list)):
            if len(mw_item) == 2 and isinstance(mw_item[1], dict):
                mw_cls, options = mw_item
                only = options.get('only')
                exclude = options.get('exclude') or options.get('except')
            else:
                mw_cls = mw_item[0]
                only = mw_item[1] if len(mw_item) > 1 else None
                exclude = mw_item[2] if len(mw_item) > 2 else None
        else:
            mw_cls, only, exclude = mw_item, None, None

        # Check action restrictions if action name is provided
        if action:
            if only:
                if isinstance(only, str):
                    only = [only]
                if action not in only:
                    continue
            if exclude:
                if isinstance(exclude, str):
                    exclude = [exclude]
                if action in exclude:
                    continue

        def make_wrapper(current_mw_cls, current_view):
            def middleware_wrapper(*args, **kwargs):
                mw = current_mw_cls()
                before_res = mw.before(request)
                if before_res is not None:
                    return make_response(before_res)
                
                res = current_view(*args, **kwargs)
                res = make_response(res)
                return mw.after(request, res)
                
            middleware_wrapper.__name__ = current_view.__name__
            return middleware_wrapper
            
        view_func = make_wrapper(mw_cls, view_func)
    return view_func


class AuthMiddleware:
    """Example authentication middleware"""
    
    def before(self, request):
        # Example: Check if user is authenticated
        # This is just a placeholder - implement your actual auth logic
        if request.endpoint and any(p in request.endpoint for p in ['login', 'register']):
            # Skip auth for login/register pages
            return None
        # Add your authentication logic here
        # For now, just allow everything through
        return None

    def after(self, request, response):
        # You can modify the response here if needed
        return response