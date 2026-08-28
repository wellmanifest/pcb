# Polityka optymalizacji trasowania

Standard nie wybiera jednej „najlepszej” płytki i nie zastępuje DRC. Definiuje,
jak porównywać poprawne warianty oraz jak odróżnić obserwację od przyczyny.

## Placement przed routingiem

Generator najpierw ustala mechanikę i funkcjonalne bloki, a dopiero potem
prowadzi miedź. Minimalna kolejność decyzji jest następująca:

1. `Edge.Cuts`, otwory, obudowa i strefy obsługi użytkownika.
2. Złącza oraz elementy naciskane lub wkładane ręcznie.
3. Moduł sterujący, z dostępem do USB, padów i otworów montażowych.
4. Regularna grupa przycisków oraz pozostałe bloki funkcjonalne.
5. Kondensatory odsprzęgające przy pinach zasilania, z krótką pętlą powrotną.
6. Dopiero po przejściu reguł placementu: fanout, szyny, sygnały i strefy.

Schemat i PCB powinny używać tych samych nazw bloków i podobnej kolejności:
zasilanie/złącze → sterownik → wejścia/przyciski → interfejs. Nie oznacza to
kopiowania współrzędnych pomiędzy SCH i PCB; oznacza zachowanie tej samej
struktury funkcjonalnej, żeby NL→DSL mogło planować blok, a nie przypadkową listę
referencji.

## Kolejność rozstrzygania

1. Kandydat zgodny z kontraktem operacji i zakresem zgody.
2. Zgodność firmware, schematu i PCB oraz kompletna łączność.
3. Zero blokujących DRC/ERC i brak regresji reguł blokujących.
4. Dopiero potem cele: mniej przelotek, mniej tranzytów wspólnych szyn, krótsze
   trasy, większa rezerwa courtyardu przy złączach, mniejsza kongestia i mniej
   naruszeń doradczych.

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

`RULE_CONNECTOR_COURTYARD_MARGIN` opisuje inny zasób: wolny korytarz wokół
złącza. Liczy wyłącznie obcą miedź, bo fanout sieci obecnej na padzie musi wejść
do własnego złącza. Zwiększenie `margin_mm` nie zmienia reguł elektrycznych i nie
zastępuje DRC; może za to ujawnić, że korytarz sygnałowy wybrano zbyt blisko
obudowy albo strefy montażowej.

Położenie złącza przechodzi trzy niezależne pomiary przed routingiem:

* `RULE_CONNECTOR_EDGE_CLEARANCE` — obrys mechaniczny złącza względem krawędzi,
* `RULE_CONNECTOR_PAD_EDGE_CLEARANCE` — zewnętrzne krawędzie jego padów,
* `RULE_TRACK_EDGE_CLEARANCE` — zewnętrzne krawędzie ścieżek i przelotek.

Każdy ma twarde minimum 2,54 mm. Courtyard/keepout 3–5 mm może być dodatkowym
celem projektu dla złącza obciążanego mechanicznie, ale nie może obniżyć żadnego
z trzech minimów ani zastąpić DRC producenta.

## Kontrfakty

Optymalizator powinien porównać ograniczony zbiór spójnych zmian:

* przypisanie funkcji do innego zgodnego elektrycznie pinu,
* przesunięcie albo obrót elementu wraz z pełnym przetrasowaniem jego sieci,
* przeniesienie wspólnej szyny do korytarza obrzeżnego,
* odsunięcie obcego korytarza od courtyardu złącza bez zmiany jego fanoutu,
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
