# Component supply chain

## Odpowiedzialność

`wellmanifest/pcb` definiuje kontrakt i znaczenie statusów. `twin-kicad`
sprawdza mechanikę plików KiCad, hashe i mapę padów. Adopter przechowuje katalog
projektu, porównuje źródło z kandydatem i uruchamia DRC/ERC oraz kontrolę
mechaniczną. Żadna z tych warstw nie może samodzielnie zaakceptować części.

## Warstwy zaufania

1. `vendor`: niemodyfikowalny checkout przypięty do pełnego commita lub wydania
   z osobnym SHA-256. Jest materiałem źródłowym, nie biblioteką projektu.
2. `verified`: wybrany MPN i rewizja datasheetu, sprawdzone pady, pin 1,
   courtyard, orientacja i model 3D. Nadal nie jest zależnością projektu.
3. `canonical`: skopiowany, wersjonowany aktyw z manifestem i hashami. Tylko ten
   poziom może otrzymać status `qualified`.

Repozytoria community zaczynają jako `quarantined`. Oficjalne źródło zaczyna z
większym zaufaniem do pochodzenia, ale nadal nie omija kontroli konkretnego MPN,
wariantu obudowy i modelu 3D.

## Bramka kandydata

Porównanie jest przyrostowe. Dług obecny po obu stronach pozostaje raportowany.
Kandydat jest blokowany, gdy:

- wprowadza nowy `library_id`, którego nie ma w katalogu;
- zwiększa użycie `quarantined`, `provisional` albo `deprecated`;
- zmienia aktyw bez zmiany wersji manifestu i SHA-256;
- mapa padów nie pokrywa footprintu dokładnie raz;
- wymagany model 3D nie istnieje, nie zgadza się hash albo nie jest związany z
  footprintem;
- źródło nie ma pełnej, niemutowalnej rewizji i licencji.

Po tej bramce nadal obowiązują footprint parity, net parity, DRC, ERC i kontrola
kolizji PCB–obudowa. Supply chain nie zastępuje żadnej z nich.

## Plan dalszej refaktoryzacji

1. Przenieść mechaniczne parsowanie modeli STEP do osobnego `twin-cad`, kiedy
   pojawi się drugi konsument poza Viewerem.
2. Dodać deterministyczny importer tworzący kandydata `vendor → canonical`, bez
   prawa automatycznej kwalifikacji.
3. Generować mini-PCB i render 3D dla każdego manifestu `qualified`.
4. Dodać dostawcę/BOM availability jako niezależną projekcję czasową; cena i
   dostępność nie mogą zmieniać kanonicznej geometrii.
5. Podłączyć KiCad StepUp/CadQuery do porównania obwiedni oraz kierunku wtyku i
   promienia gięcia kabla.
