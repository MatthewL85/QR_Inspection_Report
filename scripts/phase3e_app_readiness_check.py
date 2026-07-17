"""Run the Phase 3E app/mobile readiness checks as one focused suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


CHECKS = (
    ("App Feed Contract", "app_feed_contract_check.py"),
    ("App Shell Readiness", "app_shell_readiness_check.py"),
    ("App Health Feed Contract", "app_health_feed_contract_check.py"),
    ("App Home Feed Contract", "app_home_feed_contract_check.py"),
    ("App Capabilities Feed Contract", "app_capabilities_feed_contract_check.py"),
    ("App Mobile Surface", "app_mobile_surface_check.py"),
    ("Phase 3 Manual Contract", "phase3_manual_contract_check.py"),
)


def main() -> int:
    failures: list[tuple[str, int]] = []

    print("Phase 3E app/mobile readiness check")
    print(f"- Project root: {PROJECT_ROOT}")
    print(f"- Checks queued: {len(CHECKS)}")

    for label, script_name in CHECKS:
        script_path = PROJECT_ROOT / "scripts" / script_name
        print(f"\n== {label} ==")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

        if result.returncode != 0:
            failures.append((label, result.returncode))

    if failures:
        print("\nFAILED")
        for label, code in failures:
            print(f"- {label}: exit code {code}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
