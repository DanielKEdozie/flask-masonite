class PaymentError(Exception):
    """Base class for payment exceptions."""
    pass

class PaymentConfigError(PaymentError):
    """Raised when configuration is invalid."""
    pass

class PaymentProviderError(PaymentError):
    """Raised when a provider-specific error occurs."""
    pass

class PaymentVerificationError(PaymentError):
    """Raised when payment verification fails."""
    pass
