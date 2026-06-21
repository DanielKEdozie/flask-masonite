from setuptools import setup, find_packages

setup(
    name='Flask-Payment',
    version='1.0.0',
    description='Multi-provider payment extension for Flask.',
    author='Antigravity',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'requests',
    ],
)
