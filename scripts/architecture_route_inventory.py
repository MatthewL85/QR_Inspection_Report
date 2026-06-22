r"""Print the active LogixPM route inventory.

This is a read-only architecture helper. It loads the app factory and prints
the currently registered routes grouped by blueprint, so legacy cleanup can be
checked against what the app actually uses.

Run from the project root:
    .\venv\Scripts\python.exe scripts\architecture_route_inventory.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from app import create_app

    app = create_app()
    grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for rule in sorted(app.url_map.iter_rules(), key=lambda item: (item.endpoint, item.rule)):
        blueprint = rule.endpoint.split(".", 1)[0] if "." in rule.endpoint else "root"
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        grouped[blueprint].append((rule.endpoint, rule.rule, methods))

    print("LogixPM Active Route Inventory")
    print(f"Blueprints: {len(app.blueprints)}")
    print(f"Routes: {len(list(app.url_map.iter_rules()))}")

    for blueprint in sorted(grouped):
        print("")
        print(f"[{blueprint}]")
        for endpoint, route, methods in grouped[blueprint]:
            print(f"- {endpoint} | {route} | {methods}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
