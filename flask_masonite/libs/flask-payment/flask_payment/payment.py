from .exceptions import PaymentConfigError, PaymentError
from .providers.paystack import PaystackProvider
from .providers.flutterwave import FlutterwaveProvider

class Payment:
    PROVIDERS = {
        'paystack': PaystackProvider,
        'flutterwave': FlutterwaveProvider,
    }

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('PAYMENT_DEFAULT_PROVIDER', 'paystack')
        app.config.setdefault('PAYMENT_PROVIDERS', {})
        
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['payment'] = self

    @property
    def provider_name(self):
        from flask import current_app
        return current_app.config.get('PAYMENT_DEFAULT_PROVIDER')

    def get_provider(self, name=None):
        from flask import current_app
        name = name or self.provider_name
        config = current_app.config.get('PAYMENT_PROVIDERS', {}).get(name)
        
        if not config:
            raise PaymentConfigError(f"No configuration found for payment provider: {name}")
            
        provider_class = self.PROVIDERS.get(name)
        if not provider_class:
            raise PaymentConfigError(f"Unsupported payment provider: {name}")
            
        return provider_class(config)

    def initialize(self, amount, email, reference, callback_url, provider=None, **kwargs):
        p = self.get_provider(provider)
        return p.initialize_payment(amount, email, reference, callback_url, **kwargs)

    def verify(self, reference, provider=None):
        p = self.get_provider(provider)
        return p.verify_payment(reference)

class FlaskPayment(Payment):
    """Alias for Payment class for consistency with other extensions."""
    pass
