import os
import sys
import click
from pathlib import Path


def create_app_structure(app_name, app_title=None, app_description=None, with_storage=None, with_user=None, with_payment=None):
    """
    Create the complete Flask-Masonite application structure with all features.
    
    Args:
        app_name (str): Name of the application to create
        app_title (str): Title of the application (optional, will prompt if not provided)
        app_description (str): Description of the application (optional, will prompt if not provided)
        with_storage (bool): Include prebuilt flask-storage library
        with_user (bool): Include prebuilt flask-user library
        with_payment (bool): Include prebuilt flask-payment library
    """
    # Get app details from user if not provided
    if not app_title:
        app_title = click.prompt(
            f"Title of the App", 
            default=app_name.replace('_', ' ').title()
        )
    
    if not app_description:
        app_description = click.prompt(
            "App description", 
            default=f"A {app_title} application built with Flask-Masonite"
        )

    if with_storage is None:
        with_storage = click.confirm("Include prebuilt library 'flask-storage'?", default=True)
    if with_user is None:
        with_user = click.confirm("Include prebuilt library 'flask-user'?", default=True)
    if with_payment is None:
        with_payment = click.confirm("Include prebuilt library 'flask-payment'?", default=True)
    
    # Create main project directory
    project_dir = Path('.')
    
    # Create inner application directory named after the app
    app_dir = project_dir / app_name
    app_dir.mkdir(exist_ok=True)
    
    # Copy prebuilt libraries if selected
    additional_reqs = []
    source_libs_dir = Path(__file__).parent / 'libs'
    
    if with_storage or with_user or with_payment:
        (project_dir / 'libs').mkdir(exist_ok=True)
        
    import shutil
    
    # 1. flask-storage
    if with_storage:
        src = source_libs_dir / 'flask-storage'
        dst = project_dir / 'libs' / 'flask-storage'
        if src.exists():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'build', 'dist', '*.egg-info'), dirs_exist_ok=True)
            additional_reqs.append('./libs/flask-storage')
        else:
            additional_reqs.append('git+https://github.com/DanielKEdozie/flask-storage.git')
    else:
        additional_reqs.append('git+https://github.com/DanielKEdozie/flask-storage.git')
        
    # 2. flask-user
    if with_user:
        src = source_libs_dir / 'flask-user'
        dst = project_dir / 'libs' / 'flask-user'
        if src.exists():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'build', 'dist', '*.egg-info'), dirs_exist_ok=True)
            additional_reqs.append('./libs/flask-user')
        else:
            additional_reqs.append('git+https://github.com/DanielKEdozie/flask-user.git')
    else:
        additional_reqs.append('git+https://github.com/DanielKEdozie/flask-user.git')
        
    # 3. flask-payment
    if with_payment:
        src = source_libs_dir / 'flask-payment'
        dst = project_dir / 'libs' / 'flask-payment'
        if src.exists():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'build', 'dist', '*.egg-info'), dirs_exist_ok=True)
            additional_reqs.append('./libs/flask-payment')
        else:
            additional_reqs.append('git+https://github.com/DanielKEdozie/flask-payment.git')
    else:
        additional_reqs.append('git+https://github.com/DanielKEdozie/flask-payment.git')
    
    # Create config folder inside the app directory
    (app_dir / 'config').mkdir(exist_ok=True)
    
    # Create application subdirectories inside the app directory
    (app_dir / 'controllers').mkdir(exist_ok=True)
    (app_dir / 'models').mkdir(exist_ok=True)
    (app_dir / 'templates').mkdir(exist_ok=True)
    (app_dir / 'static').mkdir(exist_ok=True)
    (app_dir / 'static' / 'css').mkdir(exist_ok=True)
    (app_dir / 'static' / 'js').mkdir(exist_ok=True)
    (app_dir / 'static' / 'images').mkdir(exist_ok=True)
    (app_dir / 'forms').mkdir(exist_ok=True)
    (app_dir / 'routes').mkdir(exist_ok=True)
    (app_dir / 'helpers').mkdir(exist_ok=True)
    (app_dir / 'migrations').mkdir(exist_ok=True)
    
    # Create __init__.py files for the app
    (app_dir / '__init__.py').write_text(create_app_init_content(app_name))
    (app_dir / 'controllers' / '__init__.py').write_text(create_controllers_init_content())
    (app_dir / 'models' / '__init__.py').write_text(create_models_init_content())
    (app_dir / 'forms' / '__init__.py').write_text('')
    (app_dir / 'routes' / '__init__.py').write_text(create_routes_init_content())
    (app_dir / 'helpers' / '__init__.py').write_text(create_helpers_init_content())
    
    # Create __init__.py files for config directory
    (app_dir / 'config' / '__init__.py').write_text('')
    
    # Create base config
    (app_dir / 'config' / 'base.py').write_text(create_base_config_content(app_name))
    
    # Create extensions file as a single Python file
    (app_dir / 'extensions.py').write_text(create_extensions_content())
    
    # Create model files
    (app_dir / 'models' / 'user.py').write_text(create_user_model_content())
    
    # Create controller files
    (app_dir / 'controllers' / 'home_controller.py').write_text(create_home_controller_content())
    (app_dir / 'controllers' / 'auth_controller.py').write_text(create_auth_controller_content())
    
    # Create form files
    (app_dir / 'forms' / 'auth_forms.py').write_text(create_auth_forms_content())
    
    # Create template files
    (app_dir / 'templates' / 'base.html').write_text(create_base_template_content(app_title))
    (app_dir / 'templates' / 'index.html').write_text(create_index_template_content(app_title, app_description))
    (app_dir / 'templates' / 'login.html').write_text(create_login_template_content())
    (app_dir / 'templates' / 'signup.html').write_text(create_signup_template_content())
    (app_dir / 'templates' / 'profile.html').write_text(create_profile_template_content())
    (app_dir / 'templates' / 'dashboard.html').write_text(create_dashboard_template_content())
    (app_dir / 'templates' / 'docs.html').write_text(create_docs_template_content())
    
    # Create CSS file
    (app_dir / 'static' / 'css' / 'style.css').write_text(create_css_content())
    
    # Create run.py at project root level (CWD)
    (project_dir / 'run.py').write_text(create_run_content(app_name))
    
    # Create requirements.txt at project root level (CWD)
    (project_dir / 'requirements.txt').write_text(create_requirements_content(additional_reqs))
    
    click.echo(click.style(f"\nFlask-Masonite application '{app_name}' has been created successfully!", fg='green'))
    click.echo(f"\nDirectory structure:")
    click.echo(f"|-- run.py")
    click.echo(f"|-- requirements.txt")
    if with_storage or with_user or with_payment:
        click.echo(f"|-- libs/")
        if with_storage:
            click.echo(f"|   |-- flask-storage/")
        if with_user:
            click.echo(f"|   |-- flask-user/")
        if with_payment:
            click.echo(f"|   \\-- flask-payment/")
    click.echo(f"\\-- {app_name}/")
    click.echo(f"    |-- __init__.py")
    click.echo(f"    |-- extensions.py")
    click.echo(f"    |-- config/")
    click.echo(f"    |   |-- __init__.py")
    click.echo(f"    |   \\-- base.py")
    click.echo(f"    |-- routes/")
    click.echo(f"    |   \\-- __init__.py")
    click.echo(f"    |-- helpers/")
    click.echo(f"    |   \\-- __init__.py")
    click.echo(f"    |-- controllers/")
    click.echo(f"    |   |-- __init__.py")
    click.echo(f"    |   |-- home_controller.py")
    click.echo(f"    |   \\-- auth_controller.py")
    click.echo(f"    |-- models/")
    click.echo(f"    |   |-- __init__.py")
    click.echo(f"    |   \\-- user.py")
    click.echo(f"    |-- forms/")
    click.echo(f"    |   |-- __init__.py")
    click.echo(f"    |   \\-- auth_forms.py")
    click.echo(f"    |-- templates/")
    click.echo(f"    |   |-- base.html")
    click.echo(f"    |   |-- index.html")
    click.echo(f"    |   |-- login.html")
    click.echo(f"    |   |-- signup.html")
    click.echo(f"    |   |-- profile.html")
    click.echo(f"    |   |-- dashboard.html")
    click.echo(f"    |   \\-- docs.html")
    click.echo(f"    |-- static/")
    click.echo(f"    |   |-- css/")
    click.echo(f"    |   |   \\-- style.css")
    click.echo(f"    |   |-- js/")
    click.echo(f"    |   \\-- images/")
    click.echo(f"    \\-- migrations/")


def create_blueprint_structure(blueprint_name, project_root='.'):
    """
    Create a Flask-Masonite blueprint structure.
    
    Args:
        blueprint_name (str): Name of the blueprint to create
        project_root (str): Root directory of the project (default is current directory)
    """
    project_dir = Path(project_root)
    # Find the app package directory (any directory containing '__init__.py' and 'controllers/')
    app_dirs = [d for d in project_dir.iterdir() if d.is_dir() and (d / 'controllers').exists() and (d / '__init__.py').exists()]
    if not app_dirs:
        click.echo(click.style(f"Error: Could not find application package in {project_root}", fg='red'))
        return
    
    app_dir = app_dirs[0]
    blueprint_dir = app_dir / 'blueprints' / blueprint_name
    blueprint_dir.mkdir(parents=True, exist_ok=True)
    
    # Create blueprint subdirectories
    (blueprint_dir / 'controllers').mkdir(exist_ok=True)
    (blueprint_dir / 'models').mkdir(exist_ok=True)
    (blueprint_dir / 'templates').mkdir(exist_ok=True)
    (blueprint_dir / 'static').mkdir(exist_ok=True)
    
    # Create __init__.py files
    (blueprint_dir / '__init__.py').write_text(create_blueprint_init_content(blueprint_name))
    (blueprint_dir / 'controllers' / '__init__.py').write_text(create_blueprint_controllers_init_content(blueprint_name))
    (blueprint_dir / 'models' / '__init__.py').write_text(create_blueprint_models_init_content(blueprint_name))
    
    # Create a basic controller for the blueprint
    (blueprint_dir / 'controllers' / f'{blueprint_name}_controller.py').write_text(
        create_blueprint_controller_content(blueprint_name)
    )
    
    # Create a basic template
    (blueprint_dir / 'templates' / f'{blueprint_name}.html').write_text(
        create_blueprint_template_content(blueprint_name)
    )
    
    click.echo(click.style(f"Flask-Masonite blueprint '{blueprint_name}' has been created successfully!", fg='green'))
    print(f"\nBlueprint structure created in: {blueprint_dir}")
    print(f"Directory structure:")
    print(f"{blueprint_dir.name}/")
    print(f"├── __init__.py")
    print(f"├── controllers/")
    print(f"│   ├── __init__.py")
    print(f"│   └── {blueprint_name}_controller.py")
    print(f"├── models/")
    print(f"│   └── __init__.py")
    print(f"├── templates/")
    print(f"│   └── {blueprint_name}.html")
    print(f"└── static/")


def create_app_init_content(app_name):
    return f'''from flask import Flask
from .config.base import BaseConfig
from .extensions import db, init_extensions

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    
    # Initialize extensions
    init_extensions(app)

    # Import models after initializing db
    from .models.user import User, UserAuth

    # Register blueprints
    from .controllers import bp as main_bp
    app.register_blueprint(main_bp)

    # Initialize Flask-Masonite with the app
    try:
        from flask_masonite import FlaskMasonite
        flask_masonite = FlaskMasonite(app)
        
        # Register routes using the unified interface
        from .routes import create_routes
        routes = create_routes()
        app.register_routes(routes)
        
    except ImportError as e:
        # If flask_masonite is not available, continue without it
        print(f"Warning: Could not import flask_masonite: {{e}}")
        pass
    except Exception as e:
        print(f"Error setting up Flask-Masonite: {{e}}")
        pass

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
'''


def create_controllers_init_content():
    return '''from flask import Blueprint, render_template
from flask_masonite import Controller

# Create a blueprint for traditional Flask routes (if needed)
bp = Blueprint('main', __name__)

class HomeController(Controller):
    def index(self):
        return render_template('index.html')
    
    def about(self):
        return {'message': 'About Us page'}
    
    def docs(self):
        return render_template('docs.html')

class ProductController(Controller):
    def index(self):
        return {'message': 'Products listing'}
    
    def show(self, id):
        return {'id': id, 'message': f'Product {id}'}

class CartController(Controller):
    def index(self):
        return {'message': 'Shopping cart'}

class OrderController(Controller):
    def index(self):
        return {'message': 'My orders'}
    
    def show(self, id):
        return {'id': id, 'message': f'Order {id}'}
'''


def create_models_init_content():
    return '''from .user import User

__all__ = ['User']
'''


def create_routes_init_content():
    return '''from flask_masonite import RouteCollection, Route

def create_routes():
    """Define and return all application routes."""
    
    # Basic routes with names
    basic_routes = [
        Route.get('/', 'HomeController@index', name='home'),
        Route.get('/about', 'HomeController@about', name='about'),
        Route.get('/docs', 'HomeController@docs', name='docs'),  # Documentation route
        Route.get('/products', 'ProductController@index', name='products.index'),
        Route.get('/products/<int:id>', 'ProductController@show', name='products.show'),
        Route.get('/cart', 'CartController@index', name='cart.index'),
        Route.get('/orders', 'OrderController@index', name='orders.index'),
        Route.get('/orders/<int:id>', 'OrderController@show', name='orders.show'),
    ]
    
    # Authentication routes
    auth_routes = [
        Route.get('/login', 'AuthController@login', name='login'),
        Route.post('/login', 'AuthController@login', name='login.post'),
        Route.get('/register', 'AuthController@register', name='register'),
        Route.post('/register', 'AuthController@register', name='register.post'),
        Route.get('/logout', 'AuthController@logout', name='logout'),
        Route.get('/profile', 'AuthController@profile', name='profile'),
        Route.get('/dashboard', 'AuthController@dashboard', name='dashboard'),
    ]
    
    # Group API routes with prefix
    api_routes = [
        Route.get('/api/users', 'UserController@index', name='api.users.index'),
        Route.post('/api/users', 'UserController@store', name='api.users.store'),
        Route.get('/api/users/<int:id>', 'UserController@show', name='api.users.show'),
        Route.put('/api/users/<int:id>', 'UserController@update', name='api.users.update'),
        Route.delete('/api/users/<int:id>', 'UserController@destroy', name='api.users.destroy'),
    ]
    
    # Group the API routes under /v1 prefix
    grouped_api_routes = Route.group(api_routes, prefix='/v1', name_prefix='api.v1')
    
    # Combine all routes
    all_routes = basic_routes + auth_routes + grouped_api_routes
    
    # Create a RouteCollection with the defined routes
    route_collection = RouteCollection(all_routes)
    return route_collection
'''


def create_helpers_init_content():
    return '''# Helper functions and classes go here
'''


def create_base_config_content(app_name):
    return f'''import os


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Controller paths configuration
    CONTROLLER_PATHS = [
        '{app_name}.controllers',
    ]
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
'''


def create_user_model_content():
    return '''from datetime import datetime
from flask_login import UserMixin
from ..extensions import db, bcrypt


class User(db.Model, UserMixin):
    """
    User model representing the user profile.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-one relationship with UserAuth
    auth = db.relationship(
        'UserAuth',
        back_populates='user',
        uselist=False,
        lazy='joined',
        cascade='all, delete-orphan'
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

    def serialize(self):
        """Serialize the user object for JSON responses."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class UserAuth(db.Model):
    """
    Stores hashed credentials for a User.
    """
    __tablename__ = 'user_auth'

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    _password = db.Column('password', db.String(255), nullable=False)

    user = db.relationship('User', back_populates='auth')

    def __init__(self, user, password):
        self.user = user
        self.password = password

    @property
    def password(self):
        raise AttributeError('password is a write-only field')

    @password.setter
    def password(self, plain_text):
        self._password = bcrypt.generate_password_hash(plain_text).decode('utf-8')

    def verify_password(self, plain_text):
        return bcrypt.check_password_hash(self._password, plain_text)

    def __repr__(self):
        return f"<UserAuth user_id={self.user_id}>"
'''
    
def create_auth_controller_content():
    return '''from flask_masonite import Controller
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..models.user import User
from ..extensions import db
from werkzeug.security import check_password_hash


class AuthController(Controller):
    def login(self):
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = bool(request.form.get('remember_me'))

            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password) and user.is_active:
                user.update_last_login()
                login_user(user, remember=remember_me)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    def register(self):
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validation
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('signup.html')

            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return render_template('signup.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return render_template('signup.html')

            # Create new user
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('signup.html')

    def logout(self):
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))

    def profile(self):
        return render_template('profile.html', user=current_user)

    def dashboard(self):
        return render_template('dashboard.html', user=current_user)
'''


def create_auth_forms_content():
    return '''from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from ..models.user import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
'''


def create_base_template_content(app_title):
    template_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if title %}{{ title }}{% else %}APP_TITLE_PLACEHOLDER{% endif %}</title>
    <!-- Bootstrap 3.4.1 CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-default navbar-fixed-top">
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar-collapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="{{ url_for('home') }}">APP_TITLE_PLACEHOLDER</a>
            </div>
            
            <div class="collapse navbar-collapse" id="navbar-collapse">
                <ul class="nav navbar-nav navbar-right">
                    {% if current_user.is_authenticated %}
                        <li><a href="{{ url_for('dashboard') }}">Dashboard</a></li>
                        <li><a href="{{ url_for('profile') }}">Profile</a></li>
                        <li><a href="{{ url_for('logout') }}">Logout</a></li>
                    {% else %}
                        <li><a href="{{ url_for('login') }}">Login</a></li>
                        <li><a href="{{ url_for('register') }}">Sign Up</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        {% block content %}{% endblock %}
    </div>

    <div class="footer">
        <div class="container">
            <p class="text-center">&copy; {% now 'local', '%Y' %} APP_TITLE_PLACEHOLDER. All rights reserved.</p>
        </div>
    </div>

    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
    <!-- Bootstrap 3.4.1 JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
</body>
</html>
'''
    return template_str.replace('APP_TITLE_PLACEHOLDER', app_title)


def create_index_template_content(app_title, app_description):
    template_str = '''{% extends "base.html" %}

{% block content %}
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="row">
                <div class="col-md-6 col-md-offset-3">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                    {% endfor %}
                </div>
            </div>
        {% endif %}
    {% endwith %}

    <!-- Center App Name and Tagline -->
    <div class="jumbotron text-center">
        <div class="container">
            <h1 class="display-3">APP_TITLE_PLACEHOLDER</h1>
            <p class="lead">APP_DESCRIPTION_PLACEHOLDER. Built with <strong>Flask-Masonite</strong>.</p>
            <p>
                <a class="btn btn-primary btn-lg" href="https://github.com/yourusername/flask-masonite" target="_blank" role="button">
                    Flask-Masonite Documentation
                </a>
                <a class="btn btn-info btn-lg" href="{{ url_for('docs') }}">
                    View Documentation
                </a>
            </p>
        </div>
    </div>

    <!-- Welcome Section -->
    <div class="welcome-section">
        <h1 class="text-center">Welcome to APP_TITLE_PLACEHOLDER</h1>
        <p class="text-center lead">APP_DESCRIPTION_PLACEHOLDER.</p>
        
        {% if not current_user.is_authenticated %}
            <div class="text-center">
                <a href="{{ url_for('login') }}" class="btn btn-primary btn-lg">Get Started</a>
            </div>
        {% else %}
            <div class="text-center">
                <h3>Hello, {{ current_user.username }}!</h3>
                <p>You are logged in. Explore the features of APP_TITLE_PLACEHOLDER.</p>
            </div>
        {% endif %}
    </div>

    <!-- Feature Boxes -->
    <div class="feature-boxes">
        <div class="row">
            <div class="col-md-4">
                <div class="feature-box text-center">
                    <div class="feature-icon">
                        <span class="glyphicon glyphicon-user"></span>
                    </div>
                    <h3>User Management</h3>
                    <p>Create and manage user accounts with secure authentication.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-box text-center">
                    <div class="feature-icon">
                        <span class="glyphicon glyphicon-lock"></span>
                    </div>
                    <h3>Secure Access</h3>
                    <p>Protect your application with robust security measures.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-box text-center">
                    <div class="feature-icon">
                        <span class="glyphicon glyphicon-dashboard"></span>
                    </div>
                    <h3>Dashboard</h3>
                    <p>Access your personalized dashboard with key information.</p>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
'''
    return template_str.replace('APP_TITLE_PLACEHOLDER', app_title).replace('APP_DESCRIPTION_PLACEHOLDER', app_description)


def create_login_template_content():
    return '''{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-6 col-md-offset-3">
            <div class="card">
                <h3 class="text-center">Login to Your Account</h3>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <form method="POST" action="{{ url_for('login.post') }}">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="remember_me"> Remember Me
                            </label>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary btn-block">Login</button>
                </form>
                <div class="text-center" style="margin-top: 15px;">
                    <p>Don't have an account? <a href="{{ url_for('register') }}">Sign up</a></p>
                    <p><a href="#">Forgot Password?</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''


def create_signup_template_content():
    return '''{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-6 col-md-offset-3">
            <div class="card">
                <h3 class="text-center">Create an Account</h3>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <form method="POST" action="{{ url_for('register.post') }}">
                    <div class="form-group">
                        <label for="reg_username">Username</label>
                        <input type="text" class="form-control" id="reg_username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="reg_email">Email</label>
                        <input type="email" class="form-control" id="reg_email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="reg_password">Password</label>
                        <input type="password" class="form-control" id="reg_password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="reg_confirm_password">Confirm Password</label>
                        <input type="password" class="form-control" id="reg_confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-success btn-block">Sign Up</button>
                </form>
                <div class="text-center" style="margin-top: 15px;">
                    <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''


def create_profile_template_content():
    return '''{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-8 col-md-offset-2">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">User Profile</h3>
                </div>
                <div class="panel-body">
                    <div class="row">
                        <div class="col-md-4">
                            <img src="https://via.placeholder.com/150" alt="Profile Picture" class="img-responsive img-circle center-block">
                        </div>
                        <div class="col-md-8">
                            <h4>{{ user.username }}</h4>
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Email:</strong></td>
                                    <td>{{ user.email }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Name:</strong></td>
                                    <td>{{ user.first_name }} {{ user.last_name }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Role:</strong></td>
                                    <td>
                                        {% if user.is_admin %}
                                            <span class="label label-danger">Administrator</span>
                                        {% else %}
                                            <span class="label label-default">User</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>Member Since:</strong></td>
                                    <td>{{ user.date_joined.strftime('%B %d, %Y') }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Last Login:</strong></td>
                                    <td>{{ user.last_login.strftime('%B %d, %Y at %I:%M %p') if user.last_login else 'Never' }}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-12">
                            <h4>Account Settings</h4>
                            <form method="POST">
                                <div class="form-group">
                                    <label for="first_name">First Name</label>
                                    <input type="text" class="form-control" id="first_name" name="first_name" value="{{ user.first_name or '' }}">
                                </div>
                                <div class="form-group">
                                    <label for="last_name">Last Name</label>
                                    <input type="text" class="form-control" id="last_name" name="last_name" value="{{ user.last_name or '' }}">
                                </div>
                                <div class="form-group">
                                    <label for="email">Email</label>
                                    <input type="email" class="form-control" id="email" name="email" value="{{ user.email }}">
                                </div>
                                <div class="form-group">
                                    <label for="phone">Phone</label>
                                    <input type="tel" class="form-control" id="phone" name="phone" value="{{ user.phone or '' }}">
                                </div>
                                <button type="submit" class="btn btn-primary">Update Profile</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''


def create_dashboard_template_content():
    return '''{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h2>Dashboard</h2>
            <p>Welcome, {{ user.username }}! This is your personal dashboard.</p>
            
            <div class="row">
                <div class="col-md-3">
                    <div class="panel panel-primary">
                        <div class="panel-heading">
                            <h3 class="panel-title">Profile</h3>
                        </div>
                        <div class="panel-body text-center">
                            <h4><a href="{{ url_for('profile') }}">View Profile</a></h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="panel panel-success">
                        <div class="panel-heading">
                            <h3 class="panel-title">Settings</h3>
                        </div>
                        <div class="panel-body text-center">
                            <h4><a href="{{ url_for('profile') }}">Account Settings</a></h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="panel panel-info">
                        <div class="panel-heading">
                            <h3 class="panel-title">Messages</h3>
                        </div>
                        <div class="panel-body text-center">
                            <h4>0 New</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="panel panel-warning">
                        <div class="panel-heading">
                            <h3 class="panel-title">Activity</h3>
                        </div>
                        <div class="panel-body text-center">
                            <h4>Active</h4>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if user.is_admin %}
            <div class="row">
                <div class="col-md-12">
                    <div class="panel panel-danger">
                        <div class="panel-heading">
                            <h3 class="panel-title">Administrator Panel</h3>
                        </div>
                        <div class="panel-body">
                            <p>You have administrator privileges. Manage users and application settings.</p>
                            <a href="#" class="btn btn-danger">Manage Users</a>
                            <a href="#" class="btn btn-warning">System Settings</a>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
'''


def create_docs_template_content():
    return '''{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <div class="page-header">
                <h1>Flask-Masonite Documentation</h1>
                <p class="lead">A Masonite-inspired routing and controller engine for Flask applications</p>
            </div>
            
            <h2>Table of Contents</h2>
            <ul>
                <li><a href="#installation">Installation</a></li>
                <li><a href="#quick-start">Quick Start</a></li>
                <li><a href="#controllers">Controllers</a></li>
                <li><a href="#routing">Routing</a></li>
                <li><a href="#middleware">Middleware</a></li>
                <li><a href="#dependency-injection">Dependency Injection</a></li>
                <li><a href="#cli-tools">CLI Tools</a></li>
            </ul>
            
            <h2 id="installation">Installation</h2>
            <p>To install Flask-Masonite, simply run:</p>
            <pre><code>pip install flask-masonite</code></pre>
            
            <h2 id="quick-start">Quick Start</h2>
            <p>Here's a simple example to get you started:</p>
            <pre><code>from flask import Flask
from flask_masonite import FlaskMasonite, Controller, RouteCollection

app = Flask(__name__)

# Initialize Flask-Masonite
flask_masonite = FlaskMasonite(app)

class HomeController(Controller):
    def index(self):
        return {'message': 'Hello World!'}

# Define routes
routes = [
    Route.get('/', 'HomeController@index'),
]

# Register routes
flask_masonite.register_routes(routes)

if __name__ == '__main__':
    app.run(debug=True)</code></pre>

            <h2 id="controllers">Controllers</h2>
            <p>Controllers are classes that group related request handling logic. They allow you to organize your code better than using simple route functions.</p>
            <pre><code>from flask_masonite import Controller

class PostController(Controller):
    def index(self):
        # Logic to display all posts
        return {'posts': []}
    
    def show(self, id):
        # Logic to display a single post
        return {'post': {'id': id}}</code></pre>

            <h2 id="routing">Routing</h2>
            <p>Flask-Masonite provides a clean and expressive way to define your application routes.</p>
            <h3>Basic Routes</h3>
            <pre><code>from flask_masonite import Route

routes = [
    Route.get('/users', 'UserController@index'),
    Route.post('/users', 'UserController@store'),
    Route.put('/users/&lt;int:id&gt;', 'UserController@update'),
    Route.delete('/users/&lt;int:id&gt;', 'UserController@destroy'),
]</code></pre>
            
            <h3>Resource Routes</h3>
            <p>For RESTful controllers, you can use resource routes to automatically generate standard CRUD routes:</p>
            <pre><code># This generates all standard RESTful routes for posts
resource_routes = Route.resource('/posts', 'PostController')</code></pre>

            <h2 id="middleware">Middleware</h2>
            <p>Middleware allows you to filter HTTP requests entering your application.</p>
            <pre><code>from flask_masonite import Middleware

class AuthMiddleware(Middleware):
    def before(self):
        # Code to run before the request reaches the controller
        if not request.headers.get('Authorization'):
            return jsonify({'error': 'Unauthorized'}), 401

    def after(self, response):
        # Code to run after the controller has processed the request
        response.headers['X-Powered-By'] = 'Flask-Masonite'
        return response</code></pre>

            <h2 id="dependency-injection">Dependency Injection</h2>
            <p>Flask-Masonite includes a dependency injection system that automatically resolves class dependencies based on type hints.</p>
            <pre><code>from flask_masonite import Controller

class UserController(Controller):
    def show(self, user_service: UserService, id: int):
        # user_service will be automatically instantiated
        user = user_service.find(id)
        return {'user': user}</code></pre>

            <h2 id="cli-tools">CLI Tools</h2>
            <p>Flask-Masonite provides CLI tools to help you scaffold applications:</p>
            <pre><code>flask-masonite create-app myapp</code></pre>
            <p>This command creates a complete Flask-Masonite application structure with all necessary files and directories.</p>
        </div>
    </div>
</div>
{% endblock %}
'''


def create_css_content():
    return '''/* Custom styles for Flask-Masonite application */

body {
    padding-top: 70px;
    background-color: #f5f5f5;
}

.navbar-brand {
    font-weight: bold;
    font-size: 1.5em;
}

.card-container {
    max-width: 400px;
    margin: 50px auto;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,.1);
}

.form-group {
    margin-bottom: 20px;
}

.btn-block {
    padding: 12px;
    font-size: 16px;
}

.text-center {
    text-align: center;
}

.footer {
    margin-top: 50px;
    padding: 20px 0;
    background-color: #f8f8f8;
    border-top: 1px solid #e7e7e7;
}

.welcome-section {
    text-align: center;
    padding: 50px 20px;
}

.welcome-section h1 {
    color: #333;
    margin-bottom: 20px;
}

.welcome-section p {
    color: #666;
    font-size: 1.2em;
    max-width: 600px;
    margin: 0 auto 30px;
}

.feature-boxes {
    margin: 50px 0;
}

.feature-box {
    background: white;
    padding: 25px;
    margin: 10px 0;
    border-radius: 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,.1);
    text-align: center;
}

.feature-icon {
    font-size: 2.5em;
    color: #337ab7;
    margin-bottom: 15px;
}

.jumbotron {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 0;
    margin-bottom: 0;
}

.jumbotron h1 {
    color: #2c3e50;
    font-weight: bold;
}

.jumbotron .lead {
    color: #7f8c8d;
}

.alert {
    border-radius: 4px;
}

.panel {
    border-radius: 4px;
}

.table-borderless > tbody > tr > td,
.table-borderless > tbody > tr > th,
.table-borderless > tfoot > tr > td,
.table-borderless > tfoot > tr > th,
.table-borderless > thead > tr > td,
.table-borderless > thead > tr > th {
    border: none;
}

.label {
    font-weight: normal;
    border-radius: 0.25em;
}

.img-circle {
    border-radius: 50%;
}

.center-block {
    display: block;
    margin-left: auto;
    margin-right: auto;
}
'''


def create_extensions_content():
    return '''from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_masonite import register_extension

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt()
mail = Mail()
login_manager = LoginManager()
jwt = JWTManager()
cors = CORS()

def init_extensions(app):
    """Initialize and register all extensions with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Register extensions with flask_masonite extension manager
    register_extension('db', db)
    register_extension('migrate', migrate)
    register_extension('ma', ma)
    register_extension('bcrypt', bcrypt)
    register_extension('mail', mail)
    register_extension('login_manager', login_manager)
    register_extension('jwt_manager', jwt)
    register_extension('cors', cors)
    
    # Set up login manager
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))
'''


def create_home_controller_content():
    return '''from flask import render_template
from flask_masonite import Controller


class HomeController(Controller):
    def index(self):
        return render_template('index.html')
    
    def about(self):
        return {'message': 'About page'}
    
    def docs(self):
        return render_template('docs.html')
'''


def create_run_content(app_name):
    return f'''from {app_name} import create_app
from {app_name}.extensions import init_extensions

app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
'''


def create_requirements_content(additional_reqs=None):
    reqs = '''Flask==2.3.3
flask-masonite
Flask-SQLAlchemy==3.0.5
Flask-Marshmallow==0.15.0
Flask-Bcrypt==1.0.1
Flask-Mail==0.9.1
Flask-Login==0.6.3
Flask-JWT-Extended==4.5.3
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
python-dotenv==1.0.0
WTForms==3.0.1
Flask-WTF==1.2.1
Marshmallow==3.20.1
bcrypt==4.0.1
email-validator==2.0.0
Pillow==10.0.0
requests==2.31.0
PyJWT>=2.4
marshmallow-sqlalchemy>=0.28
'''
    if additional_reqs:
        reqs += '\n'.join(additional_reqs) + '\n'
    return reqs


def create_blueprint_init_content(blueprint_name):
    return f'''"""{blueprint_name.title()} Blueprint Module"""

from flask import Blueprint

# Create the blueprint
{blueprint_name}_bp = Blueprint(
    '{blueprint_name}', 
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Import routes to register them with the blueprint
from .controllers import *
'''


def create_blueprint_controllers_init_content(blueprint_name):
    return f'''"""Controllers for the {blueprint_name} blueprint"""

from flask_masonite import Controller


class {blueprint_name.title()}Controller(Controller):
    def index(self):
        return {{'message': 'Welcome to the {blueprint_name} blueprint!'}}
    
    def detail(self, id):
        return {{'id': id, 'message': f'Detail view for {blueprint_name} {{id}}'}}
'''


def create_blueprint_models_init_content(blueprint_name):
    return f'''"""Models for the {blueprint_name} blueprint"""

# Add models for the {blueprint_name} blueprint here
'''


def create_blueprint_controller_content(blueprint_name):
    return f'''"""{blueprint_name.title()} Controller"""

from flask_masonite import Controller


class {blueprint_name.title()}Controller(Controller):
    def index(self):
        return {{'message': 'Welcome to the {blueprint_name} blueprint!'}}
    
    def detail(self, id):
        return {{'id': id, 'message': f'Detail view for {blueprint_name} {{id}}'}}
    
    def create(self):
        return {{'message': 'Create view for {blueprint_name}'}}
    
    def edit(self, id):
        return {{'id': id, 'message': f'Edit view for {blueprint_name} {{id}}'}}
    
    def delete(self, id):
        return {{'id': id, 'message': f'Delete action for {blueprint_name} {{id}}'}}
'''


def create_blueprint_template_content(blueprint_name):
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>{blueprint_name.title()}</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h1>{blueprint_name.title()} Blueprint</h1>
        <p>Welcome to the {blueprint} section of the application.</p>
    </div>
    
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
</body>
</html>
'''


@click.group()
def cli():
    """Flask-Masonite CLI - Command Line Interface for Flask-Masonite"""
    pass


@cli.command()
@click.argument('app_name')
@click.option('--title', '-t', help='Title of the application')
@click.option('--description', '-d', help='Description of the application')
def create_app(app_name, title, description):
    """Create a new Flask-Masonite application"""
    create_app_structure(app_name, app_title=title, app_description=description)


@cli.command()
@click.argument('blueprint_name')
@click.option('--project-root', default='.', help='Root directory of the project (default: current directory)')
def create_blueprint(blueprint_name, project_root):
    """Create a new Flask-Masonite blueprint"""
    create_blueprint_structure(blueprint_name, project_root)


def to_pascal_case(s):
    if not s:
        return s
    # Convert string to PascalCase (e.g., user_controller -> UserController)
    s = s.replace('-', '_')
    parts = [p for p in s.split('_') if p]
    return ''.join(p[0].upper() + p[1:] for p in parts)


def to_snake_case(s):
    # Convert CamelCase/PascalCase to snake_case (e.g., UserController -> user_controller)
    import re
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower()


def create_controller_structure(name, directory=None, project_root='.'):
    project_dir = Path(project_root)
    
    # Strip any trailing '.py' if provided
    if name.endswith('.py'):
        name = name[:-3]
        
    # Resolve the base directory
    if directory:
        base_dir = project_dir / directory
    else:
        # Try to resolve CONTROLLER_PATHS from config/base.py located inside the app package
        config_paths = list(project_dir.glob('*/config/base.py'))
        resolved_path = None
        if config_paths and config_paths[0].exists():
            import re
            content = config_paths[0].read_text()
            # Search for CONTROLLER_PATHS = [ ... 'path' ... ]
            match = re.search(r"CONTROLLER_PATHS\s*=\s*\[\s*['\"]([^'\"]+)['\"]", content)
            if match:
                package_path = match.group(1) # e.g. 'myapp.controllers'
                # Convert package dot notation to directory path (e.g. myapp/controllers)
                resolved_path = package_path.replace('.', '/')
                
        if resolved_path:
            base_dir = project_dir / resolved_path
        else:
            # Fallback: dynamically find a package containing a controllers/ directory
            app_dirs = [d for d in project_dir.iterdir() if d.is_dir() and (d / 'controllers').exists()]
            if app_dirs:
                base_dir = app_dirs[0] / 'controllers'
            else:
                base_dir = project_dir / 'controllers'

    # Handle nested paths in the controller name (e.g. auth/LoginController or auth.LoginController)
    name = name.replace('.', '/')
    input_parts = [p for p in name.split('/') if p]
    
    # Base directory relative parts (e.g. ['app', 'controllers'])
    try:
        base_rel_parts = base_dir.relative_to(project_dir).parts
    except ValueError:
        base_rel_parts = ()
        
    # Check if input_parts starts with base_rel_parts, and strip if so
    if len(input_parts) >= len(base_rel_parts):
        starts_with_base = True
        for i in range(len(base_rel_parts)):
            if input_parts[i].lower() != base_rel_parts[i].lower():
                starts_with_base = False
                break
        if starts_with_base:
            input_parts = input_parts[len(base_rel_parts):]
            
    if not input_parts:
        click.echo(click.style("Error: Invalid controller name.", fg='red'))
        return
        
    controller_base_name = input_parts[-1]
    subdirs = input_parts[:-1]
    
    # Normalize class name and file name
    if not controller_base_name.lower().endswith('controller'):
        controller_class_name = to_pascal_case(controller_base_name) + 'Controller'
    else:
        controller_class_name = to_pascal_case(controller_base_name)
        
    controller_file_name = to_snake_case(controller_class_name) + '.py'
    
    # Target directory path
    target_dir = base_dir
    for part in subdirs:
        target_dir = target_dir / part

    # Create target directories
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files in newly created folders up to base_dir
    current_path = base_dir
    for part in subdirs:
        current_path = current_path / part
        init_file = current_path / '__init__.py'
        if not init_file.exists():
            init_file.write_text('')
            
    # File path
    file_path = target_dir / controller_file_name
    
    if file_path.exists():
        click.echo(click.style(f"Error: Controller file '{file_path}' already exists.", fg='red'))
        return
        
    # Controller boilerplate content
    boilerplate = f'''from flask_masonite import Controller

class {controller_class_name}(Controller):
    def index(self):
        return {{"message": "Hello from {controller_class_name}"}}
'''

    file_path.write_text(boilerplate)
    
    # Expose in package's __init__.py if it exists
    init_path = target_dir / '__init__.py'
    if init_path.exists():
        init_content = init_path.read_text()
        import_stmt = f"from .{to_snake_case(controller_class_name)} import {controller_class_name}"
        if import_stmt not in init_content:
            if init_content.strip():
                new_init_content = init_content.strip() + f"\n{import_stmt}\n"
            else:
                new_init_content = f"{import_stmt}\n"
            init_path.write_text(new_init_content)
            
    click.echo(click.style(f"Controller '{controller_class_name}' successfully created at {file_path}", fg='green'))


@cli.command()
@click.argument('name')
@click.option('--directory', '-d', help='The directory to create the controller in')
@click.option('--project-root', default='.', help='Root directory of the project (default: current directory)')
def create_controller(name, directory, project_root):
    """Create a new Flask-Masonite controller"""
    create_controller_structure(name, directory, project_root)


if __name__ == '__main__':
    cli()