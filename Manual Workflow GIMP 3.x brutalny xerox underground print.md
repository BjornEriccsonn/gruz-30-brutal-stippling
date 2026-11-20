**==🔴by GRUZ_30==**
## 1. Ustawienia projektu

1. `Plik > Nowy`. Wybierz docelowy format i **600 ppi**. A5 w 600 ppi to ok. 3496 × 4961 px. A5 w 300 ppi to 1748 × 2480 px (wystarczy, jeśli nie robisz drobnego stipplingu).
2. Ustaw tryb **RGB**: `Obraz > Tryb > RGB`. Obraz będzie szary po desaturacji, ale filtry (Szum HSV, Koloryzacja) będą działać.
3. Precyzja (opcjonalnie): `Obraz > Precyzja > 8-bit integer`. Jeśli nie widzisz tej opcji, pomiń ten krok, bo domyślne nowe obrazy mają już 8 bitów i gamma sRGB.
4. Zaplanuj **margines min. 5 mm** po bokach. Laser nie drukuje do krawędzi. Elementy do spadu i czarne ramki skanu albo odpuść, albo dodaj później na ksero lub przy składaniu zina.
5. Od razu zapisz XCF (`Plik > Zapisz jako`) i zapisuj kolejne wersje (v1, v2...).

**Scalanie filtrów (NDE).** W GIMP-ie 3 filtry nakładają się jako edytowalny stos efektów, a nie od razu na piksele. Gdy robisz szum, rozmycie i próg jeden po drugim, po każdym kroku scal filtry z warstwą: kliknij warstwę prawym przyciskiem i wybierz **Scal filtry**. Jeśli takiej opcji nie widzisz, użyj `Warstwa > Nowa z widocznego` i ukryj starą warstwę. Inaczej wynik będzie inny, niż pokazuje podgląd.

## 2. Obróbka materiału źródłowego (każdy element osobno)

Każde zdjęcie stockowe lub rycina ląduje na osobnej warstwie w pliku kolażu, ale obrabiasz je pojedynczo.

1. **Kadr i skala.** Skaluj element do docelowej wielkości w kolażu teraz, nie później. Użyj `Narzędzia > Narzędzia transformacji > Skaluj` z interpolacją Cubic lub NoHalo (zmniejszanie) i LoHalo (powiększanie).
2. **Desaturacja.** `Kolory > Desaturacja > Luminancja`. Obraz zostaje w trybie RGB.
3. **Kontrast, wersja standardowa** (płaskie tony, ryciny, krajobrazy). Najpierw `Kolory > Poziomy`: czarny punkt 35, gamma 1,00, biały punkt 220. Potem `Kolory > Jasność-kontrast`: kontrast +40 do +60, jasność 0. To zastępuje krzywą S i zjada środkowe szarości. Jeśli masz pola liczbowe w oknie Krzywe, możesz zamiast tego ustawić dwa punkty: 64 → 30 i 192 → 225.
4. **Kontrast, wersja dla ciała i mięśni.** Mocny kontrast ścina modelunek do czarnych plam, więc zamiast kroku 3 zrób: `Kolory > Cienie-światła` (cienie +50 do +70, światła 0 do -20), potem `Kolory > Poziomy` (czarny punkt 5-10, gamma 1,3-1,6, biały punkt 235-245). Nie dodawaj Jasność-kontrast.
5. **Wyostrzanie.** `Filtry > Poprawianie > Maska wyostrzająca`. Pola mogą się nazywać „odchylenie standardowe” (promień) i „skala” (ilość). Wartości startowe dla zdjęć i rycin: odchylenie standardowe 4, skala 1,5, próg 0. Dla modelunku (ciało, mięśnie): odchylenie 30, skala 0,7, próg 0. Próg zostaw na 0, bo jego podniesienie pomija drobne różnice. Pozostałe warianty są w tabeli poniżej.

Ustawienia kontrastu do wyboru:

| Efekt | Poziomy (czarny / biały) | Jasność-kontrast |
| --- | --- | --- |
| Łagodny | 20 / 235 | +20 |
| Średni (start) | 35 / 220 | +50 |
| Mocny | 55 / 200 | +70 |

Ustawienia maski wyostrzającej:

| Cel | Odchylenie standardowe | Skala |
| --- | --- | --- |
| Drobne detale i kontury (zdjęcia stockowe, ryciny) | 3-6 | 1-2 |
| Modelunek (mięśnie, fałdy, twarze) | 20-40 | 0,5-1 |
| Delikatne odświeżenie | 1-2 | 0,5 |

Zdjęcie z mięśniami możesz wyostrzyć dwa razy: najpierw szeroko (30 / 0,7), potem wąsko (4 / 1). Wyostrzaj po Cieniach-światłach i Poziomach, a przed rasteryzacją.

Ryciny i stare druki mają już własny raster, więc przy skalowaniu bywa mora. Zmiękcz je lekko rozmyciem 0,5-1 px przed binaryzacją i dopiero potem ścinaj próg. Nie rastruj ich drugi raz Newsprintem.

## 3. Stippling

1. **Skopiuj element do osobnego pliku.** Zaznacz warstwę z elementem (już po desaturacji i kontraście z kroku 2), `Edycja > Kopiuj`, potem `Edycja > Wklej jako > Nowy obraz`. Tryb indeksowany zmienia cały obraz, a nie jedną warstwę, dlatego robisz to w osobnym oknie.
2. **Zmniejsz do połowy.** `Obraz > Skaluj obraz`, zmień jednostkę na procenty i wpisz 50 w szerokość i wysokość (łańcuch zablokowany), interpolacja Cubic.
3. **Rozjaśnij.** `Kolory > Poziomy`, środkowy suwak (gamma) na 1,3-1,5. Stippling wychodzi ciemniejszy niż oryginał.
4. **Zamień na punkty.** `Obraz > Tryb > Indeksowany`, zaznacz „Użyj czarno-białej palety (1 bit)”, a w polu dithering kolorów wybierz **Floyd-Steinberg** (organiczne, robaczkowate punkty) albo Pozycyjny (regularniejszy). Kliknij Konwertuj. Obraz od razu składa się z czarnych i białych punktów.
5. **Wróć do RGB.** `Obraz > Tryb > RGB`.
6. **Powiększ dwukrotnie bez wygładzania.** `Obraz > Skaluj obraz`, 200% szerokości i wysokości, interpolacja **Brak (None)**. Każdy punkt ma teraz 2×2 px, czyli wielkość, którą laser drukuje wiarygodnie. Jeśli wolisz grubszy punkt, w kroku 2 zmniejsz do 33%, a w kroku 6 powiększ do 300% (punkty 3×3 px).
7. **Wklej do kolażu.** `Edycja > Kopiuj`, wróć do pliku kolażu, `Edycja > Wklej jako > Nowa warstwa` i ułóż w miejscu oryginału. Oryginalną warstwę ukryj.
8. **Opcjonalnie nieregularne punkty:** Rozmycie gaussowskie 0,7 px (oba pola X i Y), potem `Kolory > Próg` na ok. 128. Scal filtry.
   