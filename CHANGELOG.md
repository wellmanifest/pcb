# Changelog

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
