# Flask-Masonite

A powerful Masonite-inspired routing and controller engine for Flask applications. Flask-Masonite enhances Flask with a more structured, intuitive architecture that improves developer productivity and application maintainability.

## Key Features

- **Masonite-Style Routing**: Expressive routing syntax inspired by Masonite's elegant design
- **Modular Controller Architecture**: Organize application logic into reusable controllers
- **CLI Tooling**: Command-line utilities for scaffolding applications and components
- **Authentication System**: Comprehensive user authentication and management system
- **Component-Based Structure**: Clean separation of concerns with models, views, and controllers
- **Modern UI Foundation**: Responsive templates built with Bootstrap 3.4.1
- **ORM Integration**: Seamless SQLAlchemy ORM support for database operations
- **Middleware Support**: Flexible request/response processing pipeline
- **Dependency Injection**: Type-hint based automatic dependency resolution
- **Environment Configuration**: Easy-to-manage configuration for different environments

## Installation

You can install Flask-Masonite using pip:

```bash
pip install flask-masonite
```

Or install directly from GitHub for the latest development version:

```bash
pip install git+https://github.com/yourusername/flask-masonite.git
```

## Quick Start

Create a new Flask-Masonite application:

```bash
flask-masonite create-app myapp
```

Navigate to your app directory and start the development server:

```bash
cd myapp
python run.py
```

## Usage Guide

### Application Creation

Generate a new application skeleton:

```bash
flask-masonite create-app myapp
```

The CLI will prompt you for:
- App title (defaults to the app name)
- App description

Or you can specify them directly:

```bash
flask-masonite create-app myapp --title "My App" --description "My awesome app"
```

### Blueprint Generation

Create modular components with blueprints:

```bash
flask-masonite create-blueprint blog
```

### Controller Development

Controllers in Flask-Masonite inherit from the `Controller` base class:

```python
from flask_masonite import Controller

class PostController(Controller):
    def index(self):
        return {'posts': []}
    
    def show(self, id):
        return {'post': {'id': id}}
```

### Routing System

Define expressive routes using the Route class:

```python
from flask_masonite import RouteCollection, Route

def create_routes():
    routes = [
        Route.get('/', 'HomeController@index', name='home'),
        Route.get('/posts', 'PostController@index', name='posts.index'),
        Route.get('/posts/<int:id>', 'PostController@show', name='posts.show'),
    ]
    
    return RouteCollection(routes)
```

For RESTful controllers, use resource routes to automatically generate standard CRUD routes:

```python
from flask_masonite import Route

# This generates all standard RESTful routes for posts
resource_routes = Route.resource('/posts', 'PostController')
```

This automatically creates routes for:
- `GET /posts` → `PostController@index`
- `GET /posts/create` → `PostController@create`
- `POST /posts` → `PostController@store`
- `GET /posts/<id>` → `PostController@show`
- `GET /posts/<id>/edit` → `PostController@edit`
- `PUT/PATCH /posts/<id>` → `PostController@update`
- `DELETE /posts/<id>` → `PostController@destroy`

### Middleware

Implement request processing pipelines with middleware:

```python
from flask_masonite import Middleware

class AuthMiddleware(Middleware):
    def before(self):
        # Code to run before the request reaches the controller
        if not request.headers.get('Authorization'):
            return jsonify({'error': 'Unauthorized'}), 401

    def after(self, response):
        # Code to run after the controller has processed the request
        response.headers['X-Powered-By'] = 'Flask-Masonite'
        return response
```

### Dependency Injection

Leverage type-hint based dependency injection:

```python
from flask_masonite import Controller

class UserController(Controller):
    def show(self, user_service: UserService, id: int):
        # user_service will be automatically resolved and instantiated
        user = user_service.find(id)
        return {'user': user}
```

## Configuration

Customize Flask-Masonite through your Flask app configuration:

```python
app.config['FLASK_MASONITE_CONTROLLERS'] = [
    'myapp.controllers.UserController',
    'myapp.controllers.PostController',
]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.