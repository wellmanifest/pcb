#!/usr/bin/env python3
"""Walidacja pakietu wellmanifest/pcb.

Sprawdzamy trzy rzeczy, bo tylko razem znaczą, że standard jest jeden:
schemat i manifest wymieniają ten sam zamknięty słownik reguł, przykładowe
profile są zgodne ze schematem, a profil wbudowany w adoptera nie rozjechał
się z profilem domyślnym tego pakietu.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "pcb-style.schema.v1.json"
MANIFEST = ROOT / "dsl-manifest.json"
DEFAULT = ROOT / "examples" / "default.json"
ADOPTER_DEFAULT = "app/profiles/wellmanifest-pcb.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    schema = _load(SCHEMA)
    manifest = _load(MANIFEST)
    schema_rules = set(schema["properties"]["rules"]["properties"])
    manifest_rules = {item["id"] for item in manifest["rules"]}
    if schema_rules != manifest_rules:
        _fail(
            "słownik reguł rozjechany: schemat "
            f"{sorted(schema_rules - manifest_rules)} / manifest {sorted(manifest_rules - schema_rules)}"
        )
    print(f"✔ zamknięty słownik reguł zgodny ({len(schema_rules)} reguł)")

    if schema["properties"]["rules"].get("additionalProperties") is not False:
        _fail("schemat musi zamykać listę reguł (additionalProperties: false)")
    print("✔ nieznana reguła jest błędem profilu, nie regułą nieaktywną")

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        validator = None
        print("… jsonschema niedostępny — sprawdzam profile strukturalnie")
    else:
        validator = Draft202012Validator(schema)

    severities = set(manifest["severities"])
    for path in sorted((ROOT / "examples").glob("*.json")):
        document = _load(path)
        if validator is not None:
            errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
            if errors:
                _fail(f"{path.name}: {errors[0].message}")
        for name, rule in (document.get("rules") or {}).items():
            if name not in schema_rules:
                _fail(f"{path.name}: nieznana reguła {name}")
            if "severity" in rule and rule["severity"] not in severities:
                _fail(f"{path.name}: severity {rule['severity']!r} spoza słownika")
        print(f"✔ {path.name} zgodny z {schema['title']}")

    for item in manifest["adopters"]:
        directory = os.environ.get("ADOPTER_DIR") if item["id"].endswith("/viewer") else None
        candidate = Path(directory) / ADOPTER_DEFAULT if directory else None
        if candidate and candidate.is_file():
            if _load(candidate) != _load(DEFAULT):
                _fail(f"profil adoptera {candidate} różni się od examples/default.json")
            print(f"✔ {item['id']} używa profilu domyślnego bez lokalnej mutacji")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
