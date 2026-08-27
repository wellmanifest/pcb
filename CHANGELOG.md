# Changelog

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
