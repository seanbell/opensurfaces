import logging
from datetime import datetime


class RateLimitFilter(logging.Filter):
    """
    A logging filter that performs rate-limiting on error messages.  At most
    one error is let through every 'rate' seconds.
    """
    def __init__(self, rate=1):
        self._rate = rate
        self._now = datetime.now()

    def filter(self, record):
        if (datetime.now() - self._now).total_seconds() >= self._rate:
            self._now = datetime.now()
            return True
        return False
