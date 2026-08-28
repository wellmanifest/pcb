# Changelog

## 1.14.0

- `RULE_CONNECTOR_EDGE_CLEARANCE` wymaga co najmniej 2,54 mm (1/10 cala)
  pomiędzy całym obrysem footprintu złącza a najbliższą linią `Edge.Cuts`.
- `RULE_CONNECTOR_PAD_EDGE_CLEARANCE` stosuje to samo minimum do zewnętrznej
  krawędzi każdego pada złącza, a `RULE_TRACK_EDGE_CLEARANCE` do zewnętrznych
  krawędzi ścieżek i przelotek.
- Reguła jest blokująca i nie używa punktu kotwiczącego footprintu jako
  przybliżenia. Brak mierzalnego obrysu płytki również daje naruszenie.
- Operacja `move` może zamknąć naruszenie, ale nadal wymaga bramek DRC i braku
  regresji stylu.

## 1.13.0

- `RULE_CONNECTOR_COURTYARD_MARGIN` mierzy obce ścieżki i przelotki w obrysie
  złącza powiększonym o jawny `margin_mm`. Reguła jest doradcza: courtyard to
  polityka układu, a nie zamiennik clearance elektrycznego producenta.
- Sieci obecne na padach złącza są wyłączone z tej reguły, bo fanout musi dojść
  do własnego pada. Ich wzajemne odstępy nadal rozstrzyga DRC/netclass, więc
  profil nie może „naprawić” zwarcia samym opisem stylu.
- `reroute_component_nets` może zamknąć nową regułę, ale nadal wymaga DRC, braku
  regresji stylu i zgodności netlisty.

## 1.12.0

- `RULE_BUS_TRANSIT` odróżnia krótką odnogę kończącą się na własnym padzie od
  magistrali GND/zasilania przechodzącej przez obrys elementu. Na panel9 wspólna
  masa przechodzi tranzytem przez 27 obrysów switchy i przecina wachlarz sygnałów.
- `RULE_VIA_BUDGET` mierzy całkowitą liczbę przelotek i budżet na sieć. To cel
  optymalizacji po DRC/parity, nie zakaz przelotek: przekroczenie podpowiada, że
  wcześniejsza decyzja o pinach, położeniu albo korytarzu wymusza zmiany warstwy.
- `docs/ROUTING-OPTIMIZATION.md` definiuje kolejność bramek i celów, graf wpływów,
  kontrfakty i wymagany dowód `before/after` dla symulatora optymalizacji.
- `reassign_pin` nie żąda już `connectivity_preserved`. Operacja celowo zmienia
  pin należący do węzła, więc identyczność netlisty blokowałaby każdy poprawny
  wynik. Wiążącym dowodem pozostają DRC i zgodność firmware/SCH/PCB (`net_parity`).

## 1.11.0

- `reassign_pin`: przeniesienie sygnału na inny pin modułu. Zakres `project`, bo
  operacja dotyka trzech plików naraz — programu, schematu i płytki — a zmiana
  w jednym bez pozostałych jest rozjazdem, nie zmianą. Kolejność rozstrzyga
  kontekst: program steruje pinami naprawdę, więc to on jest źródłem.
- `remove_component`: usunięcie elementu ze schematu i z płytki. Nieodwracalne tak
  samo jak dołożenie, bo zmienia listę zakupów i montaż. Element zbędny dlatego,
  że jego funkcję pełni program — jak podciąg zastąpiony wewnętrznym pull-upem —
  przestaje być elementem, ale nie przestaje być decyzją.
- Obie żądają `net_parity`: przeniesienie sygnału i usunięcie elementu zmieniają
  netlistę **celowo**, więc dowodem nie jest jej niezmienność, tylko zgodność
  schematu z płytką po zmianie.

## 1.10.0

- Diagnostyka rozróżnia teraz, **kto wystawia kod**: `source: gate` dla kodów
  własnych bramek, `source: backend` dla kodów przekazywanych przez TwinStudio.
  Runbook należy się obu, bo użytkownik spotyka je w tym samym miejscu — na
  wyjściu tej samej operacji.
- Dziesięć kodów backendu dostało opis, w tym `EDA-DSL-VALIDATION-001`, który
  odpowiada za 24 z 25 nieudanych planowań na referencyjnym panel9. Dotąd
  planowanie kończyło się kodem bez wyjaśnienia w 40% prób.
- Walidator wymusza rozdział: kod bramki musi ją wskazywać, kod backendu nie może
  — wskazywanie którejkolwiek byłoby zmyśleniem. Wymóg „każda bramka ma
  diagnostykę" liczy odtąd tylko kody własne.

## 1.9.0

- **Zamknięty słownik diagnostyk** — trzecia noga kontraktu. Reguły mówiły, co
  jest defektem; operacje — co wolno z tym zrobić; nic nie mówiło, co znaczy
  odmowa bramki i którą operacją się ją zdejmuje. Adopter emitował piętnaście
  kodów i nie opisywał żadnego, więc `EDA_DRC_CATEGORY_REGRESSION` było ścianą,
  a nie wskazówką.
- Każda diagnostyka wiąże się z bramką (`gate`), tłumaczy, co znaczy (`means`),
  i mówi, co dalej — wskazując operacje ze słownika (`remedy_operations`) albo
  wyjaśniając, dlaczego żadna nie wystarczy (`remedy_note`).
- Walidator wymusza dwie rzeczy, których żaden opis nie pilnuje sam:
  diagnostyka nie może polecać nieznanej operacji ani wskazywać nieznanej bramki,
  a **każda bramka musi mieć co najmniej jedną diagnostykę** — bramka milcząca
  przy braku kontroli wygląda jak bramka zaliczona.
- `schemas/pcb-diagnostics.schema.v1.json`, `examples/diagnostics.json` i przykład
  negatywny.

## 1.8.0

- **Zamknięty słownik operacji.** Reguły mówiły, co jest defektem; nic nie mówiło,
  co wolno z tym zrobić. Szesnaście czasowników zmiany żyło dotąd wyłącznie
  w kodzie adoptera, więc „ta sama poprawka" mogła znaczyć co innego w powłoce,
  w REST i w MCP. `operations` zamyka tę listę tak samo, jak `rules` zamyka listę
  reguł: operacji spoza słownika nie da się zaproponować.
- Każda operacja deklaruje `changes` (co rusza: miedź, pozycję, sitodruk, netlistę,
  metadane, listę elementów), `clears` (które reguły może zamknąć), `verify` (jakie
  bramki musi przejść) i `reversible`.
- Walidator wymusza spójność: operacja nie może zamykać nieznanej reguły, żądać
  nieznanej weryfikacji, ruszać miedzi bez sprawdzenia DRC ani być nieodwracalna
  inaczej niż przez zmianę listy elementów.
- `schemas/pcb-operations.schema.v1.json`, `examples/operations.json` i przykład
  negatywny `examples/invalid-unknown-operation.json`.

## 1.7.0

- `RULE_SCH_PCB_FOOTPRINT_PARITY`: schemat i płytka muszą mówić o tym samym
  footprincie. Zgodność sieci tego nie obejmuje — netlista może zgadzać się co do
  pinu, a „Update PCB from Schematic" i tak podmieni element, bo pole `Footprint`
  w schemacie żyje własnym życiem. Ani ERC, ani DRC tego nie widzą: to rozjazd
  między dwoma plikami, więc nie należy do żadnego z nich z osobna.
- Na referencyjnym panel9 reguła od razu pokazała trzy przypadki: kondensatory
  C1 i C2 miały wpisany footprint rezystora, a złącze J1 nazwę-zaślepkę
  `RJ45_SMD_PLACEHOLDER`, której nie ma w żadnej bibliotece.
- Zakres `project`, waga domyślna `blocking` — konsekwencje są fizyczne
  (podmieniony rozstaw padów), a nie estetyczne.
- Który plik ma rację, rozstrzyga kontekst projektu przez podmiot
  `footprint-assignment`, a nie sama reguła; tam, gdzie obie nazwy istnieją,
  arbitrem jest biblioteka projektu.

## 1.6.0

- `RULE_SILK_OVER_PAD`: linia sitodruku nie wchodzi na otwór w masce pada. Farba
  na odsłoniętej miedzi nie zostaje po montażu, a jej resztki fałszują odczyt
  oznaczeń. KiCad widzi to jako `silk_over_copper` w raporcie DRC; jako reguła
  profilu ta sama rzecz daje się naprawić z powłoki i pilnować bramką regresji.
- Na referencyjnym panel9 reguła trafia dokładnie w te same 45 przypadków co DRC,
  a wzór jest pouczający: 24 to zamknięte prostokąty wokół elementów 0603,
  których pady wystają poza korpus, 18 to obrysy przycisków, 3 to moduł.
- Parametry `mask_margin_mm` i `min_segment_mm`: margines otworu w masce i próg,
  poniżej którego ogonek linii nie ma sensu i znika zamiast zostać kreską.
- Waga domyślna `advisory` — to defekt czytelności i montażu, nie łączności.
- `VERSION` wyrównany do `pcb-standard.json`; przy 1.5.0 został na 1.4.0.

## 1.5.0

- Standaryzacja zaakceptowanego długu stylistycznego: `pcb-style-baseline`
  z zamkniętym słownikiem reguł i ścisłą semantyką regresji wobec punktu
  odniesienia (commit `ef82381`, dopisane wstecz przy 1.6.0).

## 1.4.0

- `RULE_POWER_DECOUPLING`: szyna zasilania musi mieć co najmniej jeden kondensator
  do masy. Brak odsprzęgania nie daje objawu ani w netliście, ani w DRC — widać go
  dopiero na zasilanym układzie. Na referencyjnym panel9 reguła od razu pokazała,
  że ani `+3V3`, ani `+5V` nie mają żadnego kondensatora: C1–C3 siedzą na liniach
  enkodera jako filtr RC, nie jako odsprzęganie.
- Zakres `project`, waga domyślna `advisory` — to zalecenie projektowe, a nie
  defekt pliku, i nie da się go naprawić kandydatem bez dołożenia elementów.

## 1.3.0

- `dsl-manifest.json` jest teraz zgodny z `wellmanifest.dsl/manifest/v1` (0 błędów
  walidacji). Słownik domenowy — reguły, bramki, kontekst, adopterzy — przeniesiony
  do `pcb-standard.json`, na który manifest wskazuje jako źródło kanoniczne.
- Artefakty mają digesty `sha256`, sprawdzane przy każdej walidacji;
  `./project.sh digests` je przelicza.
- Przykład negatywny `examples/invalid-unknown-rule.json`: walidator wymaga, żeby
  został odrzucony — zamknięty słownik przestaje być deklaracją bez pokrycia.
- `docs/` z wyjaśnieniem, dlaczego `vocabularyKind` to `documents`, a kody ustaleń
  adoptera czekają na mapowanie razem z przyjęciem `wellmanifest/dsl`.

## 1.2.0

- Nowy schemat `wellmanifest.pcb/context/v1`: role plików, moment zmiany, tryb
  zmiany, zależności i kolejność autorytetu przy sprzeczności — propose-only.
- `RULE_TRACK_WIDTH_BY_NET`: minimalna szerokość zależna od klasy sieci
  (pierwsza pasująca klasa rozstrzyga). Słownik reguł rośnie do 15.
- Walidator sprawdza spójność manifestu i schematu kontekstu (rodzaje zależności,
  role) oraz waliduje przykłady kontekstu osobnym schematem.

## 1.1.0

- Słownik rozszerzony z 7 do 14 reguł: stackup warstw, górny limit szerokości
  ścieżki, raster minimalny, raster trasowania, kąty prowadzenia, luka
  przewód–pin w schemacie oraz zgodność sieci sch↔PCB.
- Nowy zakres `project` dla reguł wymagających obu plików naraz.
- Bramka `net_parity` z kodami `EDA_PARITY_MISMATCH` i `EDA_PARITY_NOT_RUN`.
- Udokumentowane lokalne rozszerzenie standardu w
  `<artifacts>/.wellmanifest/pcb.json` (`examples/panel9-local.json`).

## 1.0.0

- Pierwsza wersja profilu `wellmanifest.pcb/style/v1` z zamkniętym słownikiem
  siedmiu reguł dla `.kicad_pcb` i `.kicad_sch`.
- Bramka regresji `wellmanifest.pcb/style-comparison/v1`: kandydat nie może
  zwiększyć liczby naruszeń reguły blokującej; dług obecny po obu stronach nie
  blokuje decyzji.
- Nadpisanie profilu per pole, z błędem przy nieznanej nazwie reguły.
- Pierwszy adopter: `maskservice/viewer` (CLI `pcbctl`, `make style`,
  `/api/eda/style-report`, bramka akceptacji i promocji kandydata).
