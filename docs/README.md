# Dokumentacja wellmanifest/pcb

Standard opisuje **dokumenty**, nie polecenia: adopter nie wywołuje komend pakietu,
tylko wczytuje profil, manifest kontekstu i porównuje wynik ze swoim stanem.
Dlatego `documentation.vocabularyKind` to `documents`, a listy `commands`,
`errorCodes` i `criticalCodes` w `dsl-manifest.json` są puste.

Kody, którymi posługują się bramki adoptera — `EDA_STYLE_REGRESSION`,
`EDA_STYLE_NOT_RUN`, `EDA_PARITY_MISMATCH`, `EDA_PARITY_NOT_RUN` — należą do
przestrzeni adoptera i używają podkreśleń, więc nie pasują do wzorca
`findingCode` z `wellmanifest.dsl/manifest/v1`. Nie przepisujemy ich na siłę:
mapowanie powstanie razem z przyjęciem `wellmanifest/dsl` (ticket-001), żeby
jedno zdarzenie nie miało dwóch nazw.

- `ERROR/` — opisy kodów blokujących, gdy powstanie mapowanie.
- `CRITICAL/` — opisy kodów krytycznych, gdy powstanie mapowanie.
