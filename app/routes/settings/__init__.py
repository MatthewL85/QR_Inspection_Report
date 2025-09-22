# SAFE bootstrap for the Settings blueprint

from flask import Blueprint

# 1) Define the blueprint FIRST so it always exists
settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

# 2) Best-effort import of submodules that register routes onto settings_bp
#    Only import modules that actually exist right now.
try:
    from . import profile  # noqa: F401
except Exception as e:
    print(f"[settings] profile routes not loaded: {e}")

try:
    from . import branding  # noqa: F401
except Exception as e:
    print(f"[settings] branding routes not loaded: {e}")

try:
    from .bank import *  # noqa
except Exception as e:
    print(f"[settings] bank routes not loaded: {e}")

try:
    from .insurance import *  # noqa
except Exception as e:
    print(f"[settings] insurance routes not loaded: {e}")

try:
    from .licenses import *  # noqa
except Exception as e:
    print(f"[settings] licenses routes not loaded: {e}")

try:
    from .emergency import *  # noqa
except Exception as e:
    print(f"[settings] emergency routes not loaded: {e}")

# If you haven’t created these yet, leave them commented or wrap in try/except:
# try:
#     from . import bank_accounts  # noqa: F401
#     from . import insurance_policies  # noqa: F401
#     from . import emergency_contacts  # noqa: F401
#     from . import licenses  # noqa: F401
# except Exception as e:
#     print(f"[settings] optional routes not loaded: {e}")
