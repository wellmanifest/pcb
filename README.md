# wellmanifest/pcb — PCB & Schematic Style Contract Standard

Deklaratywny profil „jak ma wyglądać nasza płytka”, mierzalny bez KiCada i bez
LLM, wiążący bramkę akceptacji zmiany. DRC odpowiada, czy płytkę da się
wyprodukować; ten pakiet odpowiada, czy wygląda tak, jak się umówiono.

## Po co

Reguły w rodzaju „żadnej obcej miedzi pod przyciskiem tact”, „szyna zasilania
zawsze jako `+3V3`, nigdy `3V3`”, „elementy na siatce 0,5 mm” były dotąd
intencją w promptcie i uzasadnieniem w commicie. Nie dało się ich przenieść do
innego projektu ani sprawdzić w CI. Tutaj są dokumentem, który czyta walidator,
naprawa deterministyczna i bramka decyzji.

## Kształt profilu

```json
{
  "schema_id": "wellmanifest.pcb/style/v1",
  "profile": "panel9-strict",
  "rules": {
    "RULE_ZONE_LAYER_ALLOWLIST": {"layers": ["F.Cu"]},
    "RULE_FOOTPRINT_GRID": {"severity": "blocking", "grid_mm": 0.025}
  }
}
```

Nadpisanie zmienia **pojedyncze pola** reguły; reszta zostaje z profilu
domyślnego (`examples/default.json`). Reguła spoza zamkniętego słownika to
błąd profilu — nigdy cicho nieaktywna reguła.

Kolejność wyszukiwania profilu u adoptera:

1. `$WELLMANIFEST_PCB_PROFILE`
2. `<katalog artefaktów>/.wellmanifest/pcb.json`
3. profil domyślny wbudowany w adoptera

## Słownik reguł

| Reguła | Zakres | Domyślnie | Mierzy |
|---|---|---|---|
| `RULE_LAYER_STACKUP` | pcb | blocking | liczbę i nazwy warstw miedzi |
| `RULE_NO_COPPER_UNDER_PART` | pcb | blocking | obcą miedź pod obrysem elementu z metalem |
| `RULE_ZONE_LAYER_ALLOWLIST` | pcb | blocking | strefy poza dopuszczonymi warstwami |
| `RULE_TRACK_WIDTH_MIN` | pcb | blocking | ścieżki poniżej progu procesu |
| `RULE_TRACK_WIDTH_MAX` | pcb | blocking | ścieżki powyżej górnego limitu |
| `RULE_COORDINATE_GRID` | pcb | blocking | raster minimalny — najdrobniejszy dopuszczalny krok |
| `RULE_TRACK_GRID` | pcb | advisory | końce ścieżek poza rastrem trasowania |
| `RULE_TRACK_ANGLE` | pcb | advisory | kąty prowadzenia spoza dozwolonego zbioru |
| `RULE_FOOTPRINT_GRID` | pcb | advisory | elementy poza rastrem montażowym i obrotami |
| `RULE_REFERENCE_NAMING` | pcb | advisory | oznaczenia poza konwencją litera+numer |
| `RULE_PIN_WIRE_GAP` | schematic | blocking | koniec przewodu mijający punkt pinu |
| `RULE_RAIL_LABEL_CANONICAL` | schematic | blocking | szynę zasilania pod kilkoma nazwami |
| `RULE_SIGNAL_LABEL_NAMING` | schematic | advisory | etykiety sygnałów poza konwencją |
| `RULE_SCH_PCB_NET_PARITY` | project | blocking | ten sam pin z różną siecią w sch i w PCB |

Zakres `project` obejmuje obie strony projektu naraz: reguły `pcb` i `schematic`
liczy się z jednego pliku, `project` wymaga pary `.kicad_sch` + `.kicad_pcb`.

### Raster minimalny a raster montażowy

To dwie różne rzeczy i mają osobne reguły:

- `RULE_COORDINATE_GRID.min_mm` — **raster minimalny**: nic w projekcie nie ma
  prawa być drobniejsze. Współrzędna spoza tego kroku to błąd zapisu, zwykle
  po ręcznym przesunięciu lub po generatorze.
- `RULE_FOOTPRINT_GRID.grid_mm` — **raster montażowy**: siatka, na której
  powinny stać elementy. Odstępstwo jest czytelnym długiem, nie błędem.
- `RULE_TRACK_GRID.grid_mm` — raster trasowania dla końców ścieżek.

## Bramka regresji

Kandydat na zmianę nie może **zwiększyć** liczby naruszeń reguły `blocking`
wobec źródła. Naruszenie obecne po obu stronach to dług projektu, nie regresja —
płytka z długiem nadal daje się poprawiać. Brak możliwości policzenia profilu
(np. profil nieczytelny) jest blokadą `EDA_STYLE_NOT_RUN`, nie cichym „przeszło”.

Profil jest bramką **przed** DRC i ERC, nigdy zamiast nich.

## Przyjęcie w projekcie (ADOPT)

`maskservice/viewer` — walidator, CLI i bramka decyzji:

```bash
./scripts/pcbctl.py profile
./scripts/pcbctl.py check artifacts/pcb/panel9.kicad_pcb   # kod 1 przy blokadzie
./scripts/pcbctl.py diff  źródło.kicad_pcb kandydat.kicad_pcb
make style
curl -s http://127.0.0.1:8088/api/eda/style-report/pcb/panel9.kicad_pcb
```

### Lokalne rozszerzenie standardu

Projekt zapisuje własne wartości w `<katalog artefaktów>/.wellmanifest/pcb.json`.
Plik jest **rozszerzeniem**, nie kopią: podaje tylko to, co zmienia, a resztę
dziedziczy z profilu domyślnego pakietu. Przykład z `examples/panel9-local.json`:

```json
{
  "schema_id": "wellmanifest.pcb/style/v1",
  "profile": "panel9",
  "rules": {
    "RULE_LAYER_STACKUP": {"layers": ["F.Cu", "B.Cu"], "count": 2},
    "RULE_TRACK_WIDTH_MIN": {"min_mm": 0.35},
    "RULE_TRACK_WIDTH_MAX": {"max_mm": 0.6},
    "RULE_COORDINATE_GRID": {"min_mm": 0.005},
    "RULE_ZONE_LAYER_ALLOWLIST": {"layers": []}
  }
}
```

Reguła spoza zamkniętego słownika kończy się błędem wczytania profilu, więc
literówka w nazwie nigdy nie zamienia się w regułę po cichu nieaktywną.

## Bramka zgodności sch↔PCB

`RULE_SCH_PCB_NET_PARITY` porównuje pin po pinie sieć ze schematu z siecią pada
w PCB. Wymaga `kicad-cli` do eksportu netlisty; jego brak daje
`EDA_PARITY_NOT_RUN`, czyli brak kontroli, a nie zaliczenie.

```bash
./scripts/pcbctl.py parity artifacts/pcb/panel9.kicad_sch
# panel9.kicad_sch ⟷ panel9.kicad_pcb: blocked
#   zgodne=71 rozjazd=3 niepełne=7
#   ROZJAZD  R1.1: schemat=+3V3 PCB=ENC_SW
```

`digitaltwin-run/twinstudio` — właściciel zapisu (`twinstudio.eda-change/v1`),
strumienia zdarzeń i promocji źródła. Profil jest dziś czytany po stronie
adoptera; natywne wiązanie w `kicad_dsl` jest planowane.

## Walidacja pakietu

```bash
./project.sh check
./project.sh test
```

## Placement & Governance

- `HOME`: `wellmanifest`
- `SHAPE`: `domain_pack`
- `ADOPT`: `wellmanifest/pcb`
