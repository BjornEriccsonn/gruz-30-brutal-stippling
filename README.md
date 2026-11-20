##GRUZ-30 STIPPLING — wersja 0.2

Wtyczka ma dwa polecenia:

1. PRZYGOTUJ WARSTWĘ
   Dodaje do wybranej warstwy niedestrukcyjny stos filtrów GEGL.
   Dostępne profile:
   - Rycina / ilustracja: luminancja, poziomy 35/220, kontrast 1.5,
     Unsharp Mask 4 px / 1.5.
   - Ciało / mięśnie: luminancja, Shadows-Highlights +60/-10,
     poziomy 5/240, gamma 1.4, Unsharp Mask 30 px / 0.7 oraz 4 px / 1.0.
   - Stary druk: luminancja i Gaussian Blur 0.7 px.

2. WYKONAJ STIPPLING
   Kopiuje zaznaczoną warstwę, scala filtry tylko na kopii i tworzy na niej
   punktowy raster. Warstwa źródłowa i jej filtry pozostają edytowalne.
   Można wybrać punkty 2x2 lub 3x3 px, Floyd–Steinberg albo Bayer 8x8
   oraz gamma.

UWAGI TECHNICZNE
- Filtry przygotowujące są natywnymi filtrami GEGL w GIMP 3.
- Wartości są odwzorowaniem parametrów workflow, ale nie wszystkie suwaki
  GIMP-a mają identyczną skalę w GEGL. Szczególnie kontrast +50 został
  odwzorowany jako mnożnik kontrastu 1.5.
- Redukcja obrazu do siatki stipplingu jest w tej wersji uśrednianiem bloków,
  nie interpolacją Cubic. Powiększenie do rozmiaru oryginału daje kwadratowe
  pola punktów o zadanym rozmiarze.
- Operacje GEGL mogą różnić się dostępnością/nazwami zależnie od wersji
  GIMP/GEGL. Jeśli któryś filtr nie istnieje, GIMP pokaże błąd wykonania.
- Nie testowano jeszcze w rzeczywistej instalacji Windows/GIMP użytkownika.
  Przed pracą na docelowych kolażach zrób próbę na kopii pliku.
