from decimal import Decimal
from django.conf import settings

def get_stripe_mode_from_request(request) -> str:
    """Return 'test' or 'live' based on session setting; default to 'live'."""
    mode = request.session.get('stripe_mode', 'live')
    return 'test' if mode == 'test' else 'live'


def get_stripe_keys(mode: str) -> dict:
    """Return publishable, secret, webhook keys for the given mode (live/test)."""
    if mode == 'test':
        return {
            'publishable': getattr(settings, 'STRIPE_PUBLISHABLE_KEY_TEST', ''),
            'secret': getattr(settings, 'STRIPE_SECRET_KEY_TEST', ''),
            'webhook': getattr(settings, 'STRIPE_WEBHOOK_SECRET_TEST', ''),
        }
    return {
        'publishable': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
        'secret': getattr(settings, 'STRIPE_SECRET_KEY', ''),
        'webhook': getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
    }
