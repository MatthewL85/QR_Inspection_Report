# app/utils/config_sync.py

from app.models.client import Client
from app.models.country_client_config import CountryClientConfig
from sqlalchemy.orm import Session


def apply_country_config_to_client(client: Client, db_session: Session, verbose: bool = False) -> dict:
    """
    Auto-syncs CountryClientConfig to a new Client based on (country, client_type).

    ✅ Features:
    - Applies legal/gov rules from the matched config
    - Copies currency, language, timezone, region presets
    - Attaches `country_config_id` to the client
    - Optionally logs actions for debug

    Returns:
        dict with status and config data
    """

    result = {
        "status": "not_applied",
        "config_found": False,
        "config_id": None
    }

    # 🧠 Match config based on country and client_type (e.g., OMC, HOA, MCST)
    config = CountryClientConfig.query.filter_by(
        country=client.country,
        client_type=client.client_type
    ).first()

    if not config:
        if verbose:
            print(f"[Sync] No CountryClientConfig found for {client.country} / {client.client_type}")
        return result

    # ✅ Copy selected metadata and governance defaults
    client.currency = config.currency or client.currency
    client.language = config.language or client.language
    client.timezone = extract_first_json(config.timezones)  # handle list-based JSON fields
    client.region = extract_first_json(config.regions)
    client.country_config_id = config.id

    # 🛡️ Legal/Regulatory Inheritance
    client.min_directors = config.min_directors
    client.max_directors = config.max_directors
    client.data_protection_compliance = config.data_protection_compliance

    # 📌 Commit and return
    db_session.commit()

    if verbose:
        print(f"[Sync] Applied CountryClientConfig ID={config.id} to Client ID={client.id}")

    result.update({
        "status": "applied",
        "config_found": True,
        "config_id": config.id
    })
    return result


def extract_first_json(json_encoded_string):
    """
    Attempts to parse and return the first item in a JSON-encoded list string.
    Useful for fields like timezones or regions.
    """
    import json
    if not json_encoded_string:
        return None
    try:
        parsed = json.loads(json_encoded_string)
        return parsed[0] if isinstance(parsed, list) and parsed else None
    except Exception:
        return None
