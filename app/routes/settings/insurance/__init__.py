from .. import settings_bp  # reuse /settings blueprint

# Import views so routes register
from . import index  # noqa: F401
from . import new    # noqa: F401
from . import edit   # noqa: F401
from . import delete # noqa: F401
