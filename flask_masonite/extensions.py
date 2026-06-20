"""
Extension management system for Flask-Sonite.
This module handles Flask extension registration and initialization to avoid circular imports.
"""

class ExtensionManager:
    """
    Manages the registration and initialization of Flask extensions.
    """
    
    def __init__(self):
        self.extensions = {}
    
    def register(self, name, extension):
        """
        Register an extension with a given name.
        """
        self.extensions[name] = extension
    
    def get(self, name):
        """
        Get a registered extension by name.
        """
        return self.extensions.get(name)
    
    def init_app(self, app):
        """
        Initialize all registered extensions with the Flask app.
        """
        for name, extension in self.extensions.items():
            if hasattr(extension, 'init_app'):
                extension.init_app(app)
            else:
                # If the extension is a function, call it with the app
                extension(app)


# Global extension manager instance
extension_manager = ExtensionManager()


def register_extension(name, extension):
    """
    Register an extension with the global extension manager.
    """
    extension_manager.register(name, extension)


def get_extension(name):
    """
    Get a registered extension by name.
    """
    return extension_manager.get(name)


def initialize_extension(app):
    """
    Initialize all registered extensions with the Flask app.
    """
    extension_manager.init_app(app)