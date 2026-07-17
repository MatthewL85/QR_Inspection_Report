"""Validate support ownership and production-readiness guardrails."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/support_escalation_ownership_matrix.md": (
        "Support and Escalation Ownership Matrix",
        "Core Rule",
        "Support Ownership Matrix",
        "Support Intake Rules",
        "Escalation Rules",
        "Customer Response Rules",
        "Support Severity",
        "GAR Support Rules",
        "Every production or pilot module must have an owning support role",
        "Support ownership must follow module ownership",
        "Support must be linked to the source record where possible",
        "Contractor-only support must stay inside Contractor Logix",
        "Finance and HR support must not be handled through general module notes",
        "a user can access a module or organisation they should not be allowed to use",
        "a module is being used in pilot or production without a named support owner",
        "a data exposure incident is treated as an ordinary UI bug",
        "scripts\\support_readiness_contract_check.py",
    ),
    "docs/production_readiness_gate.md": (
        "Production Readiness Gate",
        "Core Rule",
        "Readiness Levels",
        "Module Readiness Checklist",
        "Module-Specific Gates",
        "Production Blockers",
        "Pilot Rules",
        "Sign-Off Record",
        "Nothing is production-ready until the owning module can prove its access rules",
        "support and incident ownership is clear",
        "support owner and rollback owner are named",
        "a route is live but the module has no settings owner or support owner",
        "the user manual does not explain the workflow",
        "scripts\\support_readiness_contract_check.py",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/production_readiness_gate.md",
        "docs/support_escalation_ownership_matrix.md",
        "support and production readiness contracts",
        "scripts\\support_readiness_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "production readiness levels, blockers and sign-off boundaries",
        "support ownership, escalation and customer-response boundaries",
        "scripts\\support_readiness_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "support_readiness_contract_check.py",
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

    print("Support/readiness contract check")
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
