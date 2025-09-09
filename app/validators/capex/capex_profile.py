# app/validators/capex_profile.py
from jsonschema import validate, ValidationError
from app.schemas.capex.capex_profile import CAPEX_PROFILE_SCHEMA

def validate_capex_profile(data: dict):
    try:
        validate(instance=data, schema=CAPEX_PROFILE_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Invalid CAPEX profile: {e.message}")
