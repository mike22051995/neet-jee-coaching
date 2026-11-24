"""
Shared rate-limiter instance.

Keeping the Limiter here (instead of in main.py) lets route modules import
it directly for the @limiter.limit() decorator without creating a circular
import (main.py imports routers, routers import main.py's limiter → cycle).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
