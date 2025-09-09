# 📍 app/routes/auth/security/__init__.py

"""
🛡️ Security Routes
Includes all advanced security actions:
- Two-Factor Authentication (2FA)
- Token management
- Session control
"""

from .two_factor import *      
from .two_factor_setup import *         
from .verify_token import *
from .setup_2fa import *
from .verify_2fa import *
