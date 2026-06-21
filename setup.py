from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flask-masonite",
    version="0.1.0",
    author="Your Name",
    author_email="your-email@example.com",
    description="A Masonite-inspired routing and controller engine for Flask applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_GITHUB_USERNAME/flask-masonite",
    packages=find_packages(),
    package_data={
        "flask_masonite": ["libs/**/*"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.0.0",
        "Flask-SQLAlchemy>=3.0.0",
        "Flask-Marshmallow>=0.15.0",
        "Flask-Bcrypt>=1.0.0",
        "Flask-Mail>=0.9.0",
        "Flask-Login>=0.6.0",
        "Flask-JWT-Extended>=4.0.0",
        "Flask-Migrate>=4.0.0",
        "Flask-CORS>=4.0.0",
        "python-dotenv>=1.0.0",
        "WTForms>=3.0.0",
        "Marshmallow>=3.0.0",
        "bcrypt>=4.0.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flask-masonite=flask_masonite.cli:cli",
        ],
    },
)