from flask import Blueprint

onboarding_bp = Blueprint(
    "onboarding", __name__, url_prefix="/onboarding"
)

# import routes after bp to avoid circulars
from .onboarding import *  # noqa
