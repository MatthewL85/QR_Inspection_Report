"""Verify the stabilisation register lists every Phase 3 readiness gate."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.phase3_readiness_check as readiness


REGISTER_PATH = PROJECT_ROOT / "docs" / "platform_stabilisation_register.md"


def main() -> int:
    failures: list[str] = []
    content = REGISTER_PATH.read_text(encoding="utf-8")
    checked = 0
    skipped_untracked: list[str] = []

    for label, script_name in readiness.CHECKS:
        script_file = f"scripts/{script_name.split()[0]}"
        is_tracked = (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", script_file],
                cwd=PROJECT_ROOT,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            == 0
        )
        if not is_tracked and script_file != "scripts/stabilisation_register_gate_check.py":
            skipped_untracked.append(label)
            continue

        checked += 1
        script_reference = script_file.replace("/", "\\")
        if script_reference not in content:
            failures.append(f"Stabilisation register missing {label}: {script_reference}")

    for required_heading in (
        "Close-Out Status",
        "Non-Negotiable Build Rules",
        "Verification Gates",
        "Next Stabilisation Steps",
    ):
        if required_heading not in content:
            failures.append(f"Stabilisation register missing heading: {required_heading}")

    for required_phrase in (
        "Completed for this stabilisation/security close-out",
        "Deferred module-owned close-out",
        "Finance Logix security/stabilisation is intentionally deferred",
    ):
        if required_phrase not in content:
            failures.append(f"Stabilisation register missing close-out phrase: {required_phrase}")

    print("Stabilisation register gate check")
    print(f"- Register: {REGISTER_PATH.relative_to(PROJECT_ROOT)}")
    print(f"- Phase 3 tracked gates checked: {checked}")
    if skipped_untracked:
        print(f"- Untracked gates skipped: {', '.join(skipped_untracked)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
