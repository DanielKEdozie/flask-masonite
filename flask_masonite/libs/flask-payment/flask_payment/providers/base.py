from abc import ABC, abstractmethod

class BasePaymentProvider(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def initialize_payment(self, amount, email, reference, callback_url, **kwargs):
        """Initialize a payment and return the checkout URL."""
        pass

    @abstractmethod
    def verify_payment(self, reference):
        """Verify if a payment was successful."""
        pass
