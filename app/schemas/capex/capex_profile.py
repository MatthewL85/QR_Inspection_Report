# app/schemas/capex/capex_profile.py
from datetime import date

CAPEX_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "planned_budget": {"type": ["number", "null"]},
        "current_year_allocation": {"type": ["number", "null"]},
        "priority_areas": {
            "type": "array",
            "items": {"type": "string"},
            "default": []
        },
        "next_major_works": {"type": ["string", "null"]},  # ISO date "YYYY-MM-DD"
        "projects_summary": {
            "type": "object",
            "properties": {
                "by_year": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "planned_cost": {"type": "number"},
                            "approved_cost": {"type": "number"},
                            "in_progress_cost": {"type": "number"},
                            "done_cost": {"type": "number"}
                        },
                        "required": ["planned_cost","approved_cost","in_progress_cost","done_cost"]
                    }
                },
                "totals": {
                    "type": "object",
                    "properties": {
                        "planned_cost": {"type": "number"},
                        "approved_cost": {"type": "number"},
                        "in_progress_cost": {"type": "number"},
                        "done_cost": {"type": "number"}
                    },
                    "required": ["planned_cost","approved_cost","in_progress_cost","done_cost"]
                }
            },
            "required": ["by_year","totals"]
        },
        "last_updated_by": {"type": ["integer", "null"]},
        "last_updated_at": {"type": ["string", "null"]}  # ISO timestamp
    },
    "required": ["priority_areas", "projects_summary"]
}

def default_capex_profile():
    return {
        "planned_budget": None,
        "current_year_allocation": None,
        "priority_areas": [],
        "next_major_works": None,
        "projects_summary": {
            "by_year": {},
            "totals": {
                "planned_cost": 0.0,
                "approved_cost": 0.0,
                "in_progress_cost": 0.0,
                "done_cost": 0.0
            }
        },
        "last_updated_by": None,
        "last_updated_at": None
    }
