import requests
from .base import BasePaymentProvider
from ..exceptions import PaymentProviderError


class FlutterwaveProvider(BasePaymentProvider):
    def __init__(self, config):
        super().__init__(config)
        self.secret_key = config.get('SECRET_KEY')
        self.base_url = "https://api.flutterwave.com/v3"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_payment(self, amount, email, reference, callback_url, **kwargs):
        """
        Initialize a Flutterwave payment and return the hosted payment page URL.
        Flutterwave uses 'tx_ref' as the reference identifier.
        Amount is in the currency's base unit (Naira for NGN).
        """
        url = f"{self.base_url}/payments"
        payload = {
            "tx_ref": reference,
            "amount": float(amount),     # Flutterwave accepts full Naira (not kobo)
            "currency": kwargs.pop("currency", "NGN"),
            "redirect_url": callback_url,
            "customer": {
                "email": email,
                "name": kwargs.pop("customer_name", email),
                "phonenumber": kwargs.pop("phone", ""),
            },
            "customizations": {
                "title": kwargs.pop("title", "Mcllary Accessories"),
                "description": kwargs.pop("description", "Order Payment"),
            },
            **kwargs
        }

        response = requests.post(url, json=payload, headers=self._get_headers())
        data = response.json()

        if data.get("status") != "success":
            raise PaymentProviderError(
                data.get("message", "Failed to initialize Flutterwave payment")
            )

        return data["data"]["link"]

    def verify_payment(self, reference):
        """
        Verify payment by tx_ref (our internal order reference).
        Returns True only when the transaction status is 'successful'.
        """
        url = f"{self.base_url}/transactions/verify_by_reference"
        params = {"tx_ref": reference}

        response = requests.get(url, params=params, headers=self._get_headers())
        data = response.json()

        if data.get("status") != "success":
            return False

        tx_status = data.get("data", {}).get("status", "")
        return tx_status == "successful"
