# app/routes/settings/bank/__init__.py
from .. import settings_bp  # reuse the /settings blueprint

# Import views so their routes register on settings_bp
from . import index  # noqa: F401
from . import new    # noqa: F401
from . import edit   # noqa: F401
from . import delete # noqa: F401
from . import default# noqa: F401
