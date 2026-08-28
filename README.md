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
  "routing": {
    "via_cost": 320,
    "net_order": ["GP4", "GP1", "GND"]
  },
  "rules": {
    "RULE_ZONE_LAYER_ALLOWLIST": {"layers": ["F.Cu"]},
    "RULE_FOOTPRINT_GRID": {"severity": "blocking", "grid_mm": 0.025}
  }
}
```

Nadpisanie zmienia **pojedyncze pola** reguły; reszta zostaje z profilu
domyślnego (`examples/default.json`). Reguła spoza zamkniętego słownika to
błąd profilu — nigdy cicho nieaktywna reguła.

Sekcja `routing` jest wejściem optymalizatora, nie ukrytą stałą implementacji.
`via_cost` określa względny koszt zmiany warstwy (wartość `0` jest dozwolonym
kontrfaktem bez preferencji), a `net_order` jawnie rezerwuje
korytarze najpierw dla sieci o najmniejszej swobodzie. CLI, DSL i handler muszą
raportować, czy użyły profilu, czy świadomego nadpisania symulacji.

Kolejność wyszukiwania profilu u adoptera:

1. `$WELLMANIFEST_PCB_PROFILE`
2. `<katalog artefaktów>/.wellmanifest/pcb.json`
3. profil domyślny wbudowany w adoptera

## Słownik reguł

| Reguła | Zakres | Domyślnie | Mierzy |
|---|---|---|---|
| `RULE_LAYER_STACKUP` | pcb | blocking | liczbę i nazwy warstw miedzi |
| `RULE_NO_COPPER_UNDER_PART` | pcb | blocking | obcą miedź pod obrysem elementu z metalem |
| `RULE_COMPONENT_EDGE_CLEARANCE` | pcb | blocking | odległość obrysu zwykłego elementu od `Edge.Cuts`; wyjątek musi mieć reference i uzasadnienie |
| `RULE_CONNECTOR_COURTYARD_MARGIN` | pcb | advisory | obcą miedź w powiększonym obrysie złącza |
| `RULE_CONNECTOR_EDGE_CLEARANCE` | pcb | blocking | odległość obrysu złącza od `Edge.Cuts` (minimum 2,54 mm) |
| `RULE_CONNECTOR_PAD_EDGE_CLEARANCE` | pcb | blocking | odległość padów złącza od `Edge.Cuts` (minimum 2,54 mm) |
| `RULE_TRACK_EDGE_CLEARANCE` | pcb | blocking | odległość ścieżek od `Edge.Cuts` (minimum 2,54 mm) |
| `RULE_VIA_EDGE_CLEARANCE` | pcb | blocking | odległość pierścieni przelotek od `Edge.Cuts` |
| `RULE_EDGE_MOUNT_CONNECTOR_ALIGNMENT` | pcb | blocking | wyrównanie jawnych złączy krawędziowych i ich osobny próg miedzi |
| `RULE_BUS_TRANSIT` | pcb | advisory | wspólną szynę przechodzącą przez element bez zakończenia na jego padzie |
| `RULE_FOOTPRINT_INTERNAL_CONNECTIVITY` | pcb | blocking | zgodność sieci w zadeklarowanych grupach terminali zwartych wewnątrz elementu |
| `RULE_VIA_BUDGET` | pcb | advisory | całkowity budżet przelotek i budżet zmian warstwy na sieć |
| `RULE_VIA_IN_PAD` | pcb | advisory | via w padzie SMD lub nachodząca na pad bez jawnego procesu produkcyjnego |
| `RULE_SILK_OVER_PAD` | pcb | advisory | sitodruk wchodzący na otwór w masce pada |
| `RULE_ZONE_LAYER_ALLOWLIST` | pcb | blocking | strefy poza dopuszczonymi warstwami |
| `RULE_TRACK_WIDTH_MIN` | pcb | blocking | ścieżki poniżej progu procesu |
| `RULE_TRACK_WIDTH_MAX` | pcb | blocking | ścieżki powyżej górnego limitu |
| `RULE_TRACK_WIDTH_BY_NET` | pcb | blocking | ścieżki poniżej progu swojej klasy sieci |
| `RULE_COORDINATE_GRID` | pcb | blocking | raster minimalny — najdrobniejszy dopuszczalny krok |
| `RULE_TRACK_GRID` | pcb | advisory | końce ścieżek poza rastrem trasowania |
| `RULE_TRACK_ANGLE` | pcb | advisory | kąty prowadzenia spoza dozwolonego zbioru |
| `RULE_FOOTPRINT_GRID` | pcb | advisory | elementy poza rastrem montażowym i obrotami |
| `RULE_REFERENCE_NAMING` | pcb | advisory | oznaczenia poza konwencją litera+numer |
| `RULE_PIN_WIRE_GAP` | schematic | blocking | koniec przewodu mijający punkt pinu |
| `RULE_RAIL_LABEL_CANONICAL` | schematic | blocking | szynę zasilania pod kilkoma nazwami |
| `RULE_SIGNAL_LABEL_NAMING` | schematic | advisory | etykiety sygnałów poza konwencją |
| `RULE_SCH_PCB_NET_PARITY` | project | blocking | ten sam pin z różną siecią w sch i w PCB |
| `RULE_SCH_PCB_FOOTPRINT_PARITY` | project | blocking | inny footprint w schemacie i na płytce |
| `RULE_POWER_DECOUPLING` | project | advisory | szynę zasilania bez kondensatora do masy |

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

### Przelotka jest skutkiem, nie przyczyną

`RULE_VIA_BUDGET` nie mówi, że każda przelotka jest błędem. Najpierw obowiązują
łączność, DRC i zgodność projektu; dopiero wśród poprawnych wariantów mniej zmian
warstwy jest lepsze. Gdy budżet rośnie, `RULE_BUS_TRANSIT` pomaga wskazać przyczynę:
wspólna szyna prowadzona przez środek pola elementów przecina drogi sygnałowe.

Algorytm diagnozy, graf wpływów i kontrakt wyniku symulatora opisuje
[`docs/ROUTING-OPTIMIZATION.md`](docs/ROUTING-OPTIMIZATION.md).

### Parity nie zna wnętrza elementu

`RULE_SCH_PCB_NET_PARITY` porównuje nazwę sieci dla tego samego numeru pinu,
ale nie wie, które terminale są zwarte wewnątrz rzeczywistego elementu.
`RULE_FOOTPRINT_INTERNAL_CONNECTIVITY` uzupełnia ten brak. Profil projektu
deklaruje `part_pattern` oraz `terminal_groups`, na przykład poziome pary
`[["1", "3"], ["2", "4"]]` czteropadowego przycisku. Wszystkie pady grupy
muszą nieść jedną niepustą sieć; przy `require_distinct_groups: true`
dwie grupy nie mogą nieść tej samej sieci. Domyślny profil nie zgaduje
topologii części: regułę włącza się dopiero na podstawie karty katalogowej
albo udokumentowanego pomiaru.

### Margines przy złączu nie jest odstępem od własnego pada

`RULE_CONNECTOR_COURTYARD_MARGIN` powiększa obrys złącza o `margin_mm` i
raportuje w tej strefie obce ścieżki oraz przelotki. Nie odsuwa miedzi sieci,
która występuje na padach złącza — taka ścieżka musi fizycznie dojść do własnego
pada. Jej szerokość i odstęp od sąsiedniej sieci rozstrzyga DRC oraz netclass.
Rozdzielenie jest celowe: większy courtyard poprawia przestrzeń montażową i
czytelność fanoutu, ale nie może udawać elektrycznego clearance.

### Zwykłe złącze pozostaje 1/10 cala wewnątrz płytki

`RULE_CONNECTOR_EDGE_CLEARANCE` jest niezależna od miedzi i courtyardu. Mierzy
najkrótszą odległość pomiędzy obrysem footprintu złącza a liniami `Edge.Cuts`.
Wartość `min_mm` nie może być mniejsza niż `2.54`, czyli dokładnie 1/10 cala.
Punkt kotwiczący footprintu nie jest miarą: cały obrys złącza musi zmieścić się
po wewnętrznej stronie wymaganego marginesu. Brak mierzalnego `Edge.Cuts` jest
naruszeniem, a nie cichym pominięciem kontroli.

Złącze przeznaczone do montażu na krawędzi nie może udawać zwykłego wyjątku.
Jego reference występuje w `edge_mount_references` obu ogólnych reguł złącza,
a `RULE_EDGE_MOUNT_CONNECTOR_ALIGNMENT` przejmuje odpowiedzialność: sprawdza
wskazaną stronę płytki, maksymalną szczelinę obudowy i niezależne minimum
miedzi. Dzięki temu wyjątek od 2,54 mm dla korpusu nie wyłącza DFM padów.

Reguła mechaniczna nie zastępuje kontroli miedzi. Osobna
`RULE_CONNECTOR_PAD_EDGE_CLEARANCE` mierzy krawędzie padów złącza, a
`RULE_TRACK_EDGE_CLEARANCE` — krawędzie segmentów ścieżek, a
`RULE_VIA_EDGE_CLEARANCE` — pierścienie przelotek po uwzględnieniu ich średnicy.
Wszystkie progi są liczone od
najbliższego rzeczywistego obiektu, nigdy od jego środka. DRC producenta nadal
pozostaje wymaganą bramką dla stref miedzi i pełnych reguł procesu.

### Via w padzie jest decyzją produkcyjną

`RULE_VIA_IN_PAD` odróżnia `center-in-pad` od `annulus-overlap`. Oba przypadki
są widoczne, ale profil może zdecydować, czy nachodzenie samego pierścienia ma
być raportowane. Wyjątek wymaga reference, opcjonalnego numeru pada i nazwanego
procesu `filled-and-capped` albo `via-in-pad-plated-over`; samo wpisanie
`allow: true` nie jest dowodem technologii. Domyślnie reguła jest doradcza,
natomiast projekt może ją podnieść do blokującej.

## Bramka regresji

Kandydat na zmianę nie może **zwiększyć** liczby naruszeń reguły `blocking`
wobec źródła. Naruszenie obecne po obu stronach to dług projektu, nie regresja —
płytka z długiem nadal daje się poprawiać. Brak możliwości policzenia profilu
(np. profil nieczytelny) jest blokadą `EDA_STYLE_NOT_RUN`, nie cichym „przeszło”.

Profil jest bramką **przed** DRC i ERC, nigdy zamiast nich.

### Jawny baseline długu źródła

Baseline służy wyłącznie CI dla już istniejącego źródła. Nie zmniejsza liczb w
raporcie, nie zmienia `blocking` na `advisory` i nie zastępuje DRC. Dokument
`wellmanifest.pcb/style-baseline/v1` mówi jedynie: ten konkretny limit długu
został jawnie zaakceptowany, więc blokuj jego wzrost.

Każdy baseline jest związany z `id`, wersją, nazwą i SHA-256 efektywnego profilu,
pełną ścieżką względną oraz SHA-256 pliku w chwili akceptacji. Wymaga też
`accepted.by`, `accepted.at` i uzasadnienia. Zwykła kontrola blokuje wzrost reguł
`blocking`, a tryb `strict` — wzrost każdej kategorii osobno. Uszkodzony dokument, nieznana reguła,
powtórzona ścieżka albo inny profil są błędem bramki — nigdy cichym pominięciem.
Przykład: `examples/panel9-baseline.json`; schemat:
`schemas/pcb-style-baseline.schema.v1.json`.

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

## Kontekst projektu — `wellmanifest.pcb/context/v1`

Reguły mówią, jak projekt ma wyglądać. Kontekst mówi, **co jest w którym pliku,
kiedy go zmieniać i kto ma rację**, gdy dwa pliki twierdzą co innego. Bez tego
każdy nowy agent — i każdy człowiek po przerwie — zaczyna od zgadywania, bo tego
nie widać z rozszerzeń plików: to są decyzje projektowe, nie własność formatu.

Manifest leży w `<artefakty>/.wellmanifest/context.json` i odpowiada na trzy rzeczy:

```json
{
  "schema_id": "wellmanifest.pcb/context/v1",
  "files": [
    {"path": "firmware/code.py", "role": "firmware", "edit": "manual",
     "contains": "Aktywne mapowanie klawiszy na GPIO.",
     "change_when": "Zmienia się przypisanie klawisza do pinu.",
     "authoritative_for": ["gpio-mapping"]}
  ],
  "dependencies": [
    {"from": "firmware/generator-layers.py", "to": "pcb/panel9.kicad_pcb",
     "kind": "generates", "note": "Ponowne uruchomienie nadpisze ręczne trasowanie."}
  ],
  "authority": [
    {"subject": "gpio-mapping",
     "order": ["firmware/code.py", "pcb/panel9.kicad_sch", "pcb/panel9.kicad_pcb"],
     "why": "Program jako jedyny realnie steruje pinami."}
  ]
}
```

Tryby zmiany: `manual`, `twinstudio-candidate`, `manual-or-twinstudio`, `generated`.
Rodzaje zależności: `generates`, `documents`, `netlist-parity`, `renders`, `derives`.

Manifest jest **propose-only**: sprzeczność dostaje propozycję z uzasadnieniem,
a decyzję — przyjęcie, odrzucenie albo własną edycję — podejmuje człowiek. Plik
spoza zadeklarowanej kolejności daje `decidable: false`, zamiast udawać wyrok.

Walidacja jest ostra: zależność albo pozycja kolejności wskazująca plik nieopisany
w `files` to błąd manifestu, żeby nie rozjechał się z projektem po cichu.

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

## Słownik operacji

Operacje są zamkniętym słownikiem czasowników zmiany. Adopter może wykonać
tylko operację obecną w `pcb-standard.json`; sam wpis nadal nie daje zgody na
zmianę źródła.

`resize_footprint_pads` zmienia miedź oraz geometrię produkcyjną pada, dlatego
wymaga bramek DRC i stylu oraz zgodności instancji PCB z kanoniczną biblioteką
footprintu.

## Manifest DSL i słownik domenowy

Pakiet trzyma dwa dokumenty i to rozdzielenie jest celowe:

- **`dsl-manifest.json`** — manifest w rozumieniu `wellmanifest.dsl/manifest/v1`:
  własność, źródło kanoniczne, artefakty z digestami, przestrzenie nazw,
  projekcje, cykl życia, semantyka, granica LLM, polityka ustaleń i publikacji,
  poziomy zgodności oraz mapowania na inne standardy. To po nim `diff-dsl` potrafi
  porównać ten pakiet z pozostałymi.
- **`pcb-standard.json`** — słownik domenowy: reguły, bramki, kontekst i adopterzy.
  To jest źródło kanoniczne, na które manifest wskazuje.

Wcześniej wszystko siedziało w `dsl-manifest.json`, przez co plik nie spełniał
żadnego z dwóch zadań: nie był zgodny z manifestem DSL i mieszał politykę pakietu
z jego zawartością.

Digesty artefaktów są liczone z plików i sprawdzane przy każdej walidacji — to
jedyne miejsce, w którym manifest mógłby po cichu rozjechać się z repozytorium.

```bash
./project.sh check      # słownik, schematy, przykłady, digesty, manifest DSL
./project.sh digests    # przelicz digesty po zmianie artefaktu
```

Semantyka zadeklarowana wprost: `effectModel: propose-only`, `unknownPolicy: reject`,
`llm.mode: none`. Pakiet niczego nie wykonuje i nie rozmawia z modelem — opisuje
kontrakt, a decyzje podejmuje adopter.

## Walidacja pakietu

```bash
./project.sh check
./project.sh test
```

## Placement & Governance

- `HOME`: `wellmanifest`
- `SHAPE`: `domain_pack`
- `ADOPT`: `wellmanifest/pcb`
