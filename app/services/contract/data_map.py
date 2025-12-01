def build_contract_data(contract) -> dict:
    client = contract.client
    company = getattr(contract, "company", None) or getattr(client, "management_company", None)

    return {
        "company": {
            "legal_name": getattr(company, "legal_name", None),
            "trading_name": getattr(company, "trading_name", None),
            "registration_number": getattr(company, "registration_number", None),
            "vat_reg_number": getattr(company, "vat_reg_number", None),
            "email": getattr(company, "email", None),
            "phone": getattr(company, "telephone", None),
            "address": {
                "line1": getattr(company, "address_line1", None),
                "line2": getattr(company, "address_line2", None),
                "city": getattr(company, "city", None),
                "postal_code": getattr(company, "postal_code", None),
                "country": getattr(company, "country", None),
            },
            "branding": {
                "primary_hex": getattr(company, "brand_primary_color", None),
                "secondary_hex": getattr(company, "brand_secondary_color", None),
                "accent_hex": getattr(company, "brand_color", None),
                "logo_path": getattr(company, "logo_path", None),
            },
        },
        "client": {
            "name": getattr(client, "name", None),
            "registration_number": getattr(client, "registration_number", None),
            "vat_reg_number": getattr(client, "vat_reg_number", None),
            "email": getattr(client, "email", None),
            "phone": getattr(client, "telephone", None),
            "address": {
                "line1": getattr(client, "address_line1", None),
                "line2": getattr(client, "address_line2", None),
                "city": getattr(client, "city", None),
                "postal_code": getattr(client, "postal_code", None),
                "country": getattr(client, "country", None),
            },
        },
        "term": {
            "start": contract.start_date.isoformat() if contract.start_date else None,
            "end":   contract.end_date.isoformat()   if contract.end_date   else None,
        },
        "fees": {
            "base_ex_vat": float(contract.contract_value or 0),
            "vat_rate": (contract.data_json or {}).get("fees", {}).get("vat_rate", 23),
        },
    }
