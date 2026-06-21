import requests
from .base import BasePaymentProvider
from ..exceptions import PaymentProviderError

class PaystackProvider(BasePaymentProvider):
    def __init__(self, config):
        super().__init__(config)
        self.secret_key = config.get('SECRET_KEY')
        self.base_url = "https://api.paystack.co"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_payment(self, amount, email, reference, callback_url, **kwargs):
        url = f"{self.base_url}/transaction/initialize"
        payload = {
            "amount": int(amount * 100), # Paystack expects amount in kobo/cents
            "email": email,
            "reference": reference,
            "callback_url": callback_url,
            **kwargs
        }
        
        response = requests.post(url, json=payload, headers=self._get_headers())
        data = response.json()
        
        if not data.get('status'):
            raise PaymentProviderError(data.get('message', 'Failed to initialize Paystack payment'))
            
        return data['data']['authorization_url']

    def verify_payment(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self._get_headers())
        data = response.json()
        
        if not data.get('status'):
            return False
            
        return data['data']['status'] == 'success'
