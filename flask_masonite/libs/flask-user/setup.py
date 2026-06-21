from setuptools import setup, find_packages

setup(
    name             = 'flask-user',
    version          = '1.0.0',
    description      = 'JWT + Flask-Login user management extension for Flask',
    packages         = find_packages(exclude=['tests*']),
    python_requires  = '>=3.9',
    install_requires = [
        'Flask>=2.0',
        'Flask-Login>=0.6',
        'Flask-Bcrypt>=1.0',
        'Flask-Marshmallow>=0.15',
        'marshmallow>=3.0',
        'marshmallow-sqlalchemy>=0.28',
        'PyJWT>=2.4',
        'SQLAlchemy>=1.4',
        'click>=8.0',
    ],
    extras_require = {
        'dev': ['pytest', 'pytest-flask', 'faker'],
    },
    entry_points = {
        'flask.commands': [
            'user=flask_user.cli:user_cli',
        ],
    },
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
    ],
)
