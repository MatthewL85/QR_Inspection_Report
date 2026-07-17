"""Validate the pilot/live activation contract.

This protects the practical go-live rule: modules can be locally working and
still not be safe for real organisations until activation scope, roles,
support, rollback and real-data boundaries are recorded.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/pilot_live_activation_runbook.md": (
        "Pilot and Live Activation Runbook",
        "Core Rule",
        "Activation Types",
        "Activation Preflight",
        "User and Role Verification",
        "Real Data Boundary",
        "Support and Rollback",
        "Module Add-On Rule",
        "External Connector Activation",
        "Activation Sign-Off Record",
        "No module, workflow, dashboard, queue, document, external integration or GAR surface should be activated for real users",
        "support owner",
        "rollback owner",
        "Contractor Logix remains contractor-only",
        "property management company users cannot enter Contractor Logix dashboards",
        "seeded review users and seeded review records must be clearly separated",
        "GAR answers only from source records that the current user can open directly",
        "Finance Logix or HR Logix is activated before its module-owned close-out is complete",
    ),
    "docs/production_readiness_gate.md": (
        "Production Readiness Gate",
        "Pilot Rules",
        "Sign-Off Record",
        "support owner and rollback owner are named",
        "seeded review data is clearly separated from real data",
        "Nothing is production-ready until the owning module can prove its access rules",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/pilot_live_activation_runbook.md",
        "pilot and live activation must be scoped",
        "Confirm any pilot, live activation, module add-on or external connector activation",
        "a module is switched on for real users without a named activation scope, support owner or rollback owner",
        "scripts\\pilot_live_activation_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "pilot, live activation and module add-on sign-off boundaries",
        "docs/pilot_live_activation_runbook.md",
        "scripts\\pilot_live_activation_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "docs/pilot_live_activation_runbook.md",
        "Pilot and Live Activation Runbook",
        "pilot_live_activation_contract_check.py",
    ),
}


def main() -> int:
    failures: list[str] = []

    for relative_path, required_phrases in REQUIRED_REFERENCES.items():
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            failures.append(f"Missing required file: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in content:
                failures.append(f"{relative_path} is missing: {phrase}")

    print("Pilot/live activation contract check")
    print(f"- Files checked: {len(REQUIRED_REFERENCES)}")
    print(f"- References checked: {sum(len(v) for v in REQUIRED_REFERENCES.values())}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
