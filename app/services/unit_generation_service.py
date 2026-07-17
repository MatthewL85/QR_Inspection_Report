from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.client.client import Client
from app.models.members.unit import Block, Core, Unit


_SPLIT_RE = re.compile(r"[,;\n\r]+")


@dataclass(frozen=True)
class UnitSpec:
    unit_type: str
    unit_number: str
    unit_label: str
    block_name: str = ""
    core_name: str = ""
    area_name: str = ""
    block: Block | None = None
    core: Core | None = None


def _clean_name(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _to_int(value) -> int:
    try:
        parsed = int(str(value or "").replace(",", "").strip())
        return max(parsed, 0)
    except (TypeError, ValueError):
        return 0


def _split_names(value: str | None) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for raw in _SPLIT_RE.split(value or ""):
        name = _clean_name(raw)
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            names.append(name)
    return names


def _default_block_names(client: Client) -> list[str]:
    names = _split_names(client.block_names)
    count = _to_int(client.number_of_blocks)
    if names:
        return names
    if count <= 0:
        return []
    return [f"Block {chr(64 + i)}" if i <= 26 else f"Block {i}" for i in range(1, count + 1)]


def _parse_counts(value: str | None, names: list[str], total: int) -> dict[str, int]:
    if total <= 0:
        return {name: 0 for name in names}

    parts = [_clean_name(p) for p in _SPLIT_RE.split(value or "") if _clean_name(p)]
    counts: dict[str, int] = {}

    keyed: dict[str, int] = {}
    numeric: list[int] = []
    for part in parts:
        if ":" in part:
            key, raw_count = part.split(":", 1)
            keyed[_clean_name(key).lower()] = _to_int(raw_count)
        else:
            numeric.append(_to_int(part))

    for index, name in enumerate(names):
        key = name.lower()
        if key in keyed:
            counts[name] = keyed[key]
        elif len(numeric) == 1:
            counts[name] = numeric[0]
        elif index < len(numeric):
            counts[name] = numeric[index]
        else:
            counts[name] = 0

    if not any(counts.values()) and names:
        base = total // len(names)
        remainder = total % len(names)
        for index, name in enumerate(names):
            counts[name] = base + (1 if index < remainder else 0)

    return counts


def _parse_cores_per_block(value: str | None, names: list[str]) -> dict[str, int]:
    parts = [_clean_name(p) for p in _SPLIT_RE.split(value or "") if _clean_name(p)]
    if not names:
        return {}
    if not parts:
        return {name: 0 for name in names}

    keyed: dict[str, int] = {}
    numeric: list[int] = []
    for part in parts:
        if ":" in part:
            key, raw_count = part.split(":", 1)
            keyed[_clean_name(key).lower()] = _to_int(raw_count)
        else:
            numeric.append(_to_int(part))

    result: dict[str, int] = {}
    for index, name in enumerate(names):
        key = name.lower()
        if key in keyed:
            result[name] = keyed[key]
        elif len(numeric) == 1:
            result[name] = numeric[0]
        elif index < len(numeric):
            result[name] = numeric[index]
        else:
            result[name] = 0
    return result


def _block_code(name: str, index: int) -> str:
    cleaned = _clean_name(name)
    if not cleaned:
        return f"B{index}"
    if cleaned.lower().startswith("block "):
        cleaned = cleaned[6:].strip()
    return re.sub(r"[^A-Za-z0-9]+", "", cleaned).upper() or f"B{index}"


def _get_or_create_block(client: Client, name: str) -> Block:
    block = Block.query.filter_by(client_id=client.id, name=name).first()
    if block:
        return block
    block = Block(
        client_id=client.id,
        company_id=client.company_id,
        name=name,
        code=name,
        building_type="mixed-use",
        is_active=True,
    )
    db.session.add(block)
    db.session.flush()
    return block


def _get_or_create_core(block: Block, name: str) -> Core:
    core = Core.query.filter_by(block_id=block.id, name=name).first()
    if core:
        return core
    core = Core(block_id=block.id, name=name, code=name)
    db.session.add(core)
    db.session.flush()
    return core


def _existing_unit_keys(client_id: int) -> set[tuple[int, str, str, str]]:
    rows = (
        Unit.query
        .with_entities(Unit.client_id, Unit.block_name, Unit.unit_type, Unit.unit_number)
        .filter(Unit.client_id == client_id)
        .all()
    )
    return {
        (
            row.client_id,
            row.block_name or "",
            row.unit_type or "",
            row.unit_number or "",
        )
        for row in rows
    }


def _apartment_specs(client: Client, blocks: list[Block], cores_by_block: dict[int, list[Core]]) -> Iterable[UnitSpec]:
    total = _to_int(client.units_apartments)
    if total <= 0:
        return []

    block_names = [block.name for block in blocks]
    if not blocks:
        block_names = [""]

    counts = _parse_counts(client.apartments_per_block, block_names, total)
    remaining = total
    sequence = 1
    specs: list[UnitSpec] = []

    for block_index, block_name in enumerate(block_names, start=1):
        count = min(counts.get(block_name, 0), remaining)
        remaining -= count
        block = next((b for b in blocks if b.name == block_name), None)
        cores = cores_by_block.get(block.id, []) if block else []
        prefix = _block_code(block_name, block_index) if block_name else "A"
        for local_index in range(1, count + 1):
            core = cores[(local_index - 1) % len(cores)] if cores else None
            unit_number = f"{prefix}-{local_index:03d}"
            specs.append(UnitSpec(
                unit_type="Apartment",
                unit_number=unit_number,
                unit_label=f"Apartment {unit_number}",
                block_name=block_name,
                core_name=core.name if core else "",
                block=block,
                core=core,
            ))
            sequence += 1

    while remaining > 0:
        unit_number = f"A-{sequence:03d}"
        specs.append(UnitSpec("Apartment", unit_number, f"Apartment {unit_number}"))
        sequence += 1
        remaining -= 1

    return specs


def _simple_specs(unit_type: str, count: int, prefix: str, area_name: str) -> Iterable[UnitSpec]:
    return [
        UnitSpec(
            unit_type=unit_type,
            unit_number=f"{prefix}-{index:03d}",
            unit_label=f"{unit_type} {prefix}-{index:03d}",
            area_name=area_name,
        )
        for index in range(1, count + 1)
    ]


def generate_units_for_client(client: Client) -> dict:
    """
    Build real Unit rows from a saved Client/Development structure.

    Idempotency is enforced in two layers:
    - an existing-key lookup before insert; and
    - the database unique constraint on client/block/type/unit_number.
    """
    summary = {"created": 0, "skipped_existing": 0, "errors": []}
    if not client or not client.id:
        summary["errors"].append("Client must be saved before units can be generated.")
        return summary

    block_names = _default_block_names(client)
    cores_per_block = _parse_cores_per_block(client.cores_per_block, block_names)

    blocks: list[Block] = []
    cores_by_block: dict[int, list[Core]] = defaultdict(list)
    try:
        for block_name in block_names:
            block = _get_or_create_block(client, block_name)
            blocks.append(block)
            for index in range(1, cores_per_block.get(block_name, 0) + 1):
                cores_by_block[block.id].append(_get_or_create_core(block, f"Core {index}"))

        specs: list[UnitSpec] = list(_apartment_specs(client, blocks, cores_by_block))
        specs.extend(_simple_specs("Commercial", _to_int(client.units_commercial), "C", "Commercial"))

        other_total = _to_int(getattr(client, "units_other", 0)) + _to_int(client.units_houses) + _to_int(client.units_duplexes)
        specs.extend(_simple_specs("Other", other_total, "O", "Other"))

        existing = _existing_unit_keys(client.id)
        for spec in specs:
            key = (client.id, spec.block_name or "", spec.unit_type, spec.unit_number)
            if key in existing:
                summary["skipped_existing"] += 1
                continue

            unit = Unit(
                client_id=client.id,
                company_id=client.company_id,
                block_id=spec.block.id if spec.block else None,
                core_id=spec.core.id if spec.core else None,
                unit_label=spec.unit_label,
                unit_number=spec.unit_number,
                unit_name=spec.unit_label,
                unit_type=spec.unit_type,
                unit_category=spec.unit_type,
                block_name=spec.block_name or "",
                core_name=spec.core_name or "",
                area_name=spec.area_name or "",
                status="Active",
                autogenerated=True,
                is_active=True,
            )
            db.session.add(unit)
            existing.add(key)
            summary["created"] += 1

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        summary["errors"].append(f"Duplicate unit protection prevented one or more inserts: {exc.orig}")
    except Exception as exc:
        db.session.rollback()
        summary["errors"].append(str(exc))

    return summary


def grouped_units_for_client(client_id: int) -> dict[str, dict[str, list[Unit]]]:
    units = (
        Unit.query
        .filter(Unit.client_id == client_id)
        .order_by(Unit.block_name.asc(), Unit.area_name.asc(), Unit.unit_type.asc(), Unit.unit_number.asc(), Unit.unit_label.asc())
        .all()
    )

    grouped: dict[str, dict[str, list[Unit]]] = defaultdict(lambda: defaultdict(list))
    for unit in units:
        location = unit.block_name or unit.area_name or "Unassigned"
        grouped[location][unit.unit_type or "Other"].append(unit)
    return {location: dict(types) for location, types in grouped.items()}
