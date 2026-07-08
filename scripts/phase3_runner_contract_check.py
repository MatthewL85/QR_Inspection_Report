"""Validate the Phase 3 readiness runner contract.

This protects the verification layer itself. The runner is intentionally split
into full, quick and smoke-only modes so day-to-day development remains
practical while release-style review can still exercise the heavier render
smoke checks.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.phase3_readiness_check as readiness


REQUIRED_CHECK_LABELS = {
    "Architecture",
    "Module Contracts",
    "Platform System Map",
    "Archive Inventory Strict",
    "Core Platform Identity",
    "Migration Integrity",
    "Platform Documentation Contract",
    "Manual Coverage",
    "Phase 3 Manual Contract",
    "Phase 3 Runner Contract",
    "App Feed Contract",
    "App Shell Readiness",
    "App Health Feed Contract",
    "App Home Feed Contract",
    "App Capabilities Feed Contract",
    "App Company Setup Feed Contract",
    "Workflow Action Contract",
    "Notification Contract",
    "Role Dashboard Login/Render Smoke",
    "Operational Surface Render Smoke",
    "Works Command Centre Contract",
    "Queue Surface Contract",
    "Contractor Standalone Docket Contract",
    "Works Lifecycle Flow",
}


def _mode_checks(*, quick: bool = False, smoke_only: bool = False) -> tuple[str, ...]:
    if smoke_only:
        return tuple(
            label
            for label, _script_name in readiness.CHECKS
            if label in readiness.SLOW_SMOKE_CHECKS
        )
    if quick:
        return tuple(
            label
            for label, _script_name in readiness.CHECKS
            if label not in readiness.SLOW_SMOKE_CHECKS
        )
    return tuple(label for label, _script_name in readiness.CHECKS)


def main() -> int:
    failures: list[str] = []
    labels = [label for label, _script_name in readiness.CHECKS]
    label_set = set(labels)

    missing_required = sorted(REQUIRED_CHECK_LABELS.difference(label_set))
    if missing_required:
        failures.append("Missing required readiness checks: " + ", ".join(missing_required))

    duplicate_labels = sorted(label for label in label_set if labels.count(label) > 1)
    if duplicate_labels:
        failures.append("Duplicate readiness labels: " + ", ".join(duplicate_labels))

    for label, script_name in readiness.CHECKS:
        script_parts = script_name.split()
        script_path = readiness.PROJECT_ROOT / "scripts" / script_parts[0]
        if not script_path.exists():
            failures.append(f"{label} references missing script: {script_path}")
        if script_path.name == "phase3_readiness_check.py":
            failures.append(f"{label} must not recursively call phase3_readiness_check.py")

    smoke_labels = set(readiness.SLOW_SMOKE_CHECKS)
    unknown_smoke_labels = sorted(smoke_labels.difference(label_set))
    if unknown_smoke_labels:
        failures.append(
            "Slow smoke labels are not present in CHECKS: " + ", ".join(unknown_smoke_labels)
        )

    full_labels = set(_mode_checks())
    quick_labels = set(_mode_checks(quick=True))
    smoke_only_labels = set(_mode_checks(smoke_only=True))

    if not smoke_only_labels:
        failures.append("smoke-only mode must run at least one check")
    if smoke_only_labels != smoke_labels:
        failures.append("smoke-only mode must run exactly the declared slow smoke checks")
    if quick_labels.intersection(smoke_labels):
        failures.append("quick mode must not include slow smoke checks")
    if quick_labels.union(smoke_only_labels) != full_labels:
        failures.append("quick + smoke-only modes must cover the same checks as full mode")
    if quick_labels.intersection(smoke_only_labels):
        failures.append("quick and smoke-only modes must not overlap")

    timeout = readiness.CHECK_TIMEOUT_SECONDS
    if timeout < 30:
        failures.append("Default per-check timeout is too low for local Flask smoke checks")
    if readiness.FAILED_CHECK_RETRIES < 1:
        failures.append("Failed-check retry count should be at least 1 for transient DB disconnects")

    source_text = (readiness.PROJECT_ROOT / "scripts" / "phase3_readiness_check.py").read_text(
        encoding="utf-8"
    )
    for expected_arg in ("--quick", "--smoke-only", "--list"):
        if expected_arg not in source_text:
            failures.append(f"Readiness runner is missing supported argument: {expected_arg}")

    print("Phase 3 runner contract check")
    print(f"- Full checks declared: {len(full_labels)}")
    print(f"- Quick checks: {len(quick_labels)}")
    print(f"- Smoke-only checks: {len(smoke_only_labels)}")
    print(f"- Per-check timeout: {timeout}s")
    print(f"- Failed-check retries: {readiness.FAILED_CHECK_RETRIES}")
    print("- List mode checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
