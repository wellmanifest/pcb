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
BASELINE_SCHEMA = ROOT / "schemas" / "pcb-style-baseline.schema.v1.json"
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


def _check_operations(manifest: dict, rule_ids: set[str]) -> None:
    """Zamknięty słownik zmian — druga połowa kontraktu obok słownika reguł.

    Reguły mówią, co jest defektem; operacje mówią, co wolno z tym zrobić.
    Bez zamknięcia tej listy każde narzędzie może wymyślić własny czasownik
    zmiany, a wtedy „ta sama poprawka" znaczy co innego w powłoce, w REST
    i w MCP.
    """
    schema_path = ROOT / "schemas" / "pcb-operations.schema.v1.json"
    example_path = ROOT / "examples" / "operations.json"
    if not (schema_path.is_file() and example_path.is_file()):
        _fail("brak schematu albo przykładu słownika operacji")
    schema = _load(schema_path)
    declared = {item["id"] for item in manifest.get("operations") or []}
    if not declared:
        _fail("standard nie deklaruje żadnej operacji")
    enum = set(schema["$defs"]["operation"]["properties"]["id"]["enum"])
    if enum != declared:
        _fail(
            "słownik operacji rozjechany: schemat "
            f"{sorted(enum - declared)} / manifest {sorted(declared - enum)}"
        )
    changes = {item["id"] for item in manifest.get("changes") or []}
    verifications = {item["id"] for item in manifest.get("verifications") or []}
    for operation in manifest["operations"]:
        unknown = [name for name in operation["clears"] if name not in rule_ids]
        if unknown:
            _fail(f"operacja {operation['id']} zamyka nieznaną regułę {unknown[0]}")
        if operation["changes"] not in changes:
            _fail(f"operacja {operation['id']} deklaruje nieznany skutek {operation['changes']!r}")
        outside = [name for name in operation["verify"] if name not in verifications]
        if outside:
            _fail(f"operacja {operation['id']} żąda nieznanej weryfikacji {outside[0]}")
        if operation["changes"] in {"copper", "placement", "bom"} \
                and "drc_no_regression" not in operation["verify"]:
            _fail(
                f"operacja {operation['id']} rusza miedź albo listę elementów, "
                "a nie żąda sprawdzenia DRC"
            )
        if not operation["reversible"] and operation["changes"] != "bom":
            _fail(f"operacja {operation['id']} jest nieodwracalna, a nie zmienia listy elementów")
    print(f"✔ zamknięty słownik operacji zgodny ({len(declared)} operacji)")

    document = _load(example_path)
    if document.get("operations") != manifest["operations"]:
        _fail("examples/operations.json rozjechany ze standardem")
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        _fail(f"examples/operations.json: {errors[0].message}")
    print("✔ examples/operations.json zgodny z wellmanifest.pcb/operations/v1")

    negative = ROOT / "examples" / "invalid-unknown-operation.json"
    if negative.is_file():
        bad = _load(negative)
        if not list(validator.iter_errors(bad)):
            _fail("examples/invalid-unknown-operation.json przechodzi walidację, a nie powinien")
        print("✔ nieznana operacja jest błędem, nie operacją nieaktywną")


def _check_diagnostics(manifest: dict) -> None:
    """Trzecia noga kontraktu: co znaczy odmowa i którą operacją się ją zdejmuje.

    Bramka, która mówi tylko `EDA_DRC_CATEGORY_REGRESSION`, kończy rozmowę
    zamiast ją zacząć. Kod bez wyjaśnienia i bez wskazania naprawy jest kodem,
    którego nikt nie umie użyć.
    """
    schema_path = ROOT / "schemas" / "pcb-diagnostics.schema.v1.json"
    example_path = ROOT / "examples" / "diagnostics.json"
    if not (schema_path.is_file() and example_path.is_file()):
        _fail("brak schematu albo przykładu słownika diagnostyk")
    schema = _load(schema_path)
    declared = {item["id"] for item in manifest.get("diagnostics") or []}
    if not declared:
        _fail("standard nie deklaruje żadnej diagnostyki")
    enum = set(schema["$defs"]["diagnostic"]["properties"]["id"]["enum"])
    if enum != declared:
        _fail(f"słownik diagnostyk rozjechany: {sorted(enum ^ declared)}")
    gates = {item["id"] for item in manifest.get("verifications") or []}
    operations = {item["id"] for item in manifest.get("operations") or []}
    for diagnostic in manifest["diagnostics"]:
        if diagnostic["gate"] not in gates:
            _fail(f"diagnostyka {diagnostic['id']} wskazuje nieznaną bramkę "
                  f"{diagnostic['gate']!r}")
        unknown = [name for name in diagnostic["remedy_operations"] if name not in operations]
        if unknown:
            _fail(f"diagnostyka {diagnostic['id']} poleca nieznaną operację {unknown[0]}")
        if diagnostic["severity"] == "ERROR" and not diagnostic["remedy_note"]:
            _fail(f"diagnostyka {diagnostic['id']} blokuje, a nie mówi, co dalej")
    # Każda bramka musi mieć kod na wypadek, gdy się nie wykona. Bramka, która
    # milczy przy braku kontroli, wygląda jak bramka, która przeszła.
    silent = sorted(gates - {item["gate"] for item in manifest["diagnostics"]})
    if silent:
        _fail(f"bramka {silent[0]} nie ma żadnej diagnostyki — odmowa byłaby bez nazwy")
    print(f"✔ zamknięty słownik diagnostyk zgodny ({len(declared)} kodów)")

    document = _load(example_path)
    if document.get("diagnostics") != manifest["diagnostics"]:
        _fail("examples/diagnostics.json rozjechany ze standardem")
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        _fail(f"examples/diagnostics.json: {errors[0].message}")
    negative = ROOT / "examples" / "invalid-unknown-diagnostic.json"
    if negative.is_file() and not list(validator.iter_errors(_load(negative))):
        _fail("examples/invalid-unknown-diagnostic.json przechodzi walidację, a nie powinien")
    print("✔ nieznany kod jest błędem, nie kodem nieopisanym")


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
        if ("context" in path.name or "baseline" in path.name
                or "operations" in path.name or "diagnostics" in path.name
                or path.name.startswith("invalid")):
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

    baseline_schema = _load(BASELINE_SCHEMA)
    baseline_rules = set(
        baseline_schema["$defs"]["file"]["properties"]["rules"]["propertyNames"]["enum"]
    )
    if baseline_rules != manifest_rules:
        _fail(f"słownik baseline rozjechany z regułami: {sorted(baseline_rules ^ manifest_rules)}")
    if manifest.get("grammar", {}).get("baseline_schema") != baseline_schema["properties"]["schema_id"]["const"]:
        _fail("manifest i schemat baseline deklarują różne schema_id")
    baseline_example = _load(ROOT / "examples" / "panel9-baseline.json")
    if validator is not None:
        errors = sorted(Draft202012Validator(baseline_schema).iter_errors(baseline_example), key=lambda item: list(item.path))
        if errors:
            _fail(f"panel9-baseline.json: {errors[0].message}")
    paths = [entry["path"] for entry in baseline_example["files"]]
    if len(paths) != len(set(paths)):
        _fail("panel9-baseline.json zawiera tę samą ścieżkę więcej niż raz")
    print(f"✔ baseline: {len(paths)} plik(i), zamknięty słownik {len(baseline_rules)} reguł")

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

    _check_operations(manifest, manifest_rules)

    _check_diagnostics(manifest)

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
