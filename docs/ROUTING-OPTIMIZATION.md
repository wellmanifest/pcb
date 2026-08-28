# Polityka optymalizacji trasowania

Standard nie wybiera jednej „najlepszej” płytki i nie zastępuje DRC. Definiuje,
jak porównywać poprawne warianty oraz jak odróżnić obserwację od przyczyny.

## Kolejność rozstrzygania

1. Kandydat zgodny z kontraktem operacji i zakresem zgody.
2. Zgodność firmware, schematu i PCB oraz kompletna łączność.
3. Zero blokujących DRC/ERC i brak regresji reguł blokujących.
4. Dopiero potem cele: mniej przelotek, mniej tranzytów wspólnych szyn, krótsze
   trasy, mniejsza kongestia i mniej naruszeń doradczych.

Nie wolno sumować tych klas jedną wagą. Krótsza trasa nie kompensuje zwarcia,
rozpiętej sieci ani rozjazdu schematu z PCB.

## Dwie miary, jeden mechanizm

`RULE_VIA_BUDGET` mierzy skutek — zmianę warstwy. `RULE_BUS_TRANSIT` wskazuje
częstą przyczynę: GND albo zasilanie przechodzące przez pole elementów dzieli
dostępny korytarz i zmusza sygnały do przechodzenia na drugą warstwę.

Tranzyt różni się od odnogi geometrycznie:

* odnoga wchodzi w obrys i kończy się na padzie tego elementu,
* tranzyt wchodzi jedną stroną i wychodzi drugą, a żaden jego koniec nie jest
  zakończeniem na własnym padzie.

Reguły są doradcze. Przelotka może być poprawnym rozwiązaniem, a wspólna szyna
może wymagać przejścia przez dany region. Profil projektu ustala budżety i wzorce
sieci/elementów; adopter raportuje pełne znaleziska zamiast wydawać wyrok z nazwy.

## Kontrfakty

Optymalizator powinien porównać ograniczony zbiór spójnych zmian:

* przypisanie funkcji do innego zgodnego elektrycznie pinu,
* przesunięcie albo obrót elementu wraz z pełnym przetrasowaniem jego sieci,
* przeniesienie wspólnej szyny do korytarza obrzeżnego,
* zmianę kolejności trasowania w tym samym modelu ograniczeń.

Każdy wariant przechowuje wejściowe hashe, operacje, wynik wszystkich bramek,
liczby `before/after` oraz ścieżkę przyczynową, np.:

```text
GND w polu switchy → przecięcia z wachlarzem sygnałów → zmiany warstwy → przelotki
```

Wariant odrzucony jest wynikiem pomiaru, nie błędem symulatora. Raport musi
zachować powód odmowy, żeby kolejna próba nie powtarzała rozwiązania, które już
zwiększyło DRC albo zmieniło netlistę.

## Warunek wdrożenia u adoptera

Samo rozpoznanie identyfikatora reguły nie jest implementacją. Adopter potrzebuje
testów pokazujących jednocześnie:

* zero na artefakcie bez defektu,
* dodatni wynik po wstrzyknięciu tranzytu albo nadmiarowej przelotki,
* odrzucenie wariantu z lepszym kosztem, ale złamaną bramką,
* zachowanie wyniku negatywnego wraz z przyczyną.

Do tego czasu profil nie powinien aktywować nowych reguł jako warunku promocji.
