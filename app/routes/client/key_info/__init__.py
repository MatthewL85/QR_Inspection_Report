# app/routes/client/key_info/__init__.py
from __future__ import annotations
from flask import Blueprint

# Single, canonical blueprint. No url_prefix here because the view
# functions use the full absolute paths (e.g. "/clients/<id>/key-info/").
bp = Blueprint("client_key_info", __name__)

# Import side-effect to register routes on this blueprint
from . import views  # noqa: E402,F401
