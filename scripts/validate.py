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
CONTEXT_SCHEMA = ROOT / "schemas" / "pcb-context.schema.v1.json"
MANIFEST = ROOT / "dsl-manifest.json"
STANDARD = ROOT / "pcb-standard.json"
DEFAULT = ROOT / "examples" / "default.json"
ADOPTER_DEFAULT = "app/profiles/wellmanifest-pcb.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(1)


def _check_dsl_manifest() -> None:
    """Manifest DSL wobec `wellmanifest.dsl/manifest/v1` i wobec plików na dysku.

    Digesty artefaktów są jedynym miejscem, w którym manifest może po cichu
    rozjechać się z zawartością repozytorium — więc liczymy je od nowa.
    """
    import hashlib

    manifest = _load(MANIFEST)
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.is_file():
            _fail(f"manifest DSL wskazuje nieistniejący artefakt {artifact['path']}")
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != artifact["digest"]:
            _fail(f"digest {artifact['path']} nieaktualny — uruchom ./project.sh digests")
    print(f"✔ digesty {len(manifest['artifacts'])} artefaktów zgodne z plikami")

    schema_path = Path.home() / "github" / "wellmanifest" / "dsl" / "schemas" / "dsl-manifest.schema.json"
    if not schema_path.is_file():
        print("… wellmanifest/dsl niedostępny lokalnie — pominięto walidację manifestu DSL")
        return
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("… brak jsonschema — pominięto walidację manifestu DSL")
        return
    errors = list(Draft202012Validator(_load(schema_path)).iter_errors(manifest))
    if errors:
        where = "/".join(str(part) for part in errors[0].path) or "(root)"
        _fail(f"manifest DSL {where}: {errors[0].message}")
    print("✔ dsl-manifest.json zgodny z wellmanifest.dsl/manifest/v1")


def refresh_digests() -> int:
    import hashlib

    manifest = _load(MANIFEST)
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        artifact["digest"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✔ odświeżono digesty {len(manifest['artifacts'])} artefaktów")
    return 0


def main() -> int:
    if "--refresh-digests" in sys.argv:
        return refresh_digests()
    schema = _load(SCHEMA)
    manifest = _load(STANDARD)
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
    # Profile stylu i manifesty kontekstu leżą w jednym katalogu, ale mają
    # osobne schematy — mieszanie ich dawało fałszywy błąd walidacji.
    for path in sorted((ROOT / "examples").glob("*.json")):
        # Przykłady kontekstu mają własny schemat, a negatywne mają się nie
        # walidować — obie grupy mają osobne kontrole niżej.
        if "context" in path.name or path.name.startswith("invalid"):
            continue
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

    context_schema = _load(CONTEXT_SCHEMA)
    if manifest.get("context", {}).get("schema") != context_schema["properties"]["schema_id"]["const"]:
        _fail("manifest i schemat kontekstu deklarują różne schema_id")
    context_props = context_schema["properties"]
    declared_kinds = set(manifest["context"]["dependency_kinds"])
    schema_kinds = set(context_props["dependencies"]["items"]["properties"]["kind"]["enum"])
    if declared_kinds != schema_kinds:
        _fail(f"rodzaje zależności rozjechane: {sorted(declared_kinds ^ schema_kinds)}")
    declared_roles = set(manifest["context"]["roles"])
    schema_roles = set(context_props["files"]["items"]["properties"]["role"]["enum"])
    if declared_roles != schema_roles:
        _fail(f"role rozjechane: {sorted(declared_roles ^ schema_roles)}")
    print(f"✔ kontekst: {len(schema_kinds)} rodzajów zależności, {len(schema_roles)} ról")

    for path in sorted((ROOT / "examples").glob("*context*.json")):
        document = _load(path)
        if validator is not None:
            context_validator = Draft202012Validator(context_schema)
            errors = sorted(context_validator.iter_errors(document), key=lambda item: list(item.path))
            if errors:
                _fail(f"{path.name}: {errors[0].message}")
        known = {str(entry["path"]) for entry in document["files"]}
        for edge in document.get("dependencies") or []:
            for side in ("from", "to"):
                if edge[side] not in known:
                    _fail(f"{path.name}: zależność wskazuje nieopisany plik {edge[side]!r}")
        for rule in document.get("authority") or []:
            for item in rule["order"]:
                if item not in known:
                    _fail(f"{path.name}: {rule['subject']} wskazuje nieopisany plik {item!r}")
        print(f"✔ {path.name} zgodny z {context_schema['title']}")

    invalid = ROOT / "examples" / "invalid-unknown-rule.json"
    if invalid.is_file():
        document = _load(invalid)
        unknown = [name for name in document.get("rules") or {} if name not in schema_rules]
        if not unknown:
            _fail("examples/invalid-unknown-rule.json nie zawiera już nieznanej reguły — przykład przestał być negatywny")
        if validator is not None and not list(validator.iter_errors(document)):
            _fail("examples/invalid-unknown-rule.json przechodzi walidację, a nie powinien")
        print(f"✔ przykład negatywny odrzucony ({unknown[0]})")

    _check_dsl_manifest()

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
