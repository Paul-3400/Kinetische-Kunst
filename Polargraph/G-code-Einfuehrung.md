# G-code-Einführung für den Polargraphen

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 27.10.2026

Tutorial zum Projekt [Polargraph](README.md): Was G-code ist, wie PNG-Skizzen mit Inkscape (installiert auf dem MacBook Air) in G-code-Dateien umgewandelt werden und wie der Arduino diese verarbeitet. Grundlage: Quellcode-Analyse von [Pontifex42/Walldraw.ino](https://github.com/Pontifex42/Walldraw/blob/master/UNO/Code/Walldraw/Walldraw.ino).

---

## 1. Was ist G-code?

G-code ist die Sprache, mit der Maschinen Bewegungsbefehle erhalten – erfunden in den 1950er-Jahren am MIT für die ersten CNC-Fräsmaschinen, heute standardisiert (RS-274) und überall: Fräsen, Laserschneider, 3D-Drucker. G-code ist reiner Text, Zeile für Zeile. Jede Zeile besteht aus «Wörtern» – ein Buchstabe plus einer Zahl:

| Wort | Bedeutung | Beispiel |
|---|---|---|
| `G0` / `G00` | Eilgang (ohne Zeichnen) | `G00 X50 Y20` |
| `G1` / `G01` | Linearbewegung (Zeichnen) | `G01 X50 Y20` |
| `X` / `Y` / `Z` | Zielkoordinate | `X120.5 Y-30` |
| `F` | Vorschub (Geschwindigkeit) | `F300` |
| `M3`/`M5` | Zusatzfunktion ein/aus | (hier irrelevant) |

Die gute Nachricht: Der Polargraph versteht nur einen Mini-Dialekt – eigentlich nur die Koordinaten. Alles andere (`G21`, `F300`, …) liest die Firmware einfach hinweg.

## 2. Der Dialekt des Polargraphen

Die Funktion `nc()` in `Walldraw.ino` macht pro Zeile nur folgendes:

1. Zeile gross schreiben und nach `X`, `Y`, `Z` durchsuchen (Reihenfolge muss X → Y → Z sein, was Gcodetools sowieso so ausgibt).
2. **Z-Wert**: grösser 0 → Stift heben, sonst → Stift senken.
3. **X- und Y-Wert**: dorthin fahren (in Millimetern, multipliziert mit dem Skalierungsfaktor aus `1.par`).

Ein komplettes Zeichenfile – hier ein Rechteck – sieht so aus:

```gcode
G21
G90
G00 Z5.000000      <- Stift heben
G00 X-50 Y20       <- ohne Zeichnen zum Startpunkt
G01 Z-1.000000     <- Stift senken (Z <= 0)
G01 X50 Y20        <- Linie nach rechts
G01 X50 Y-30       <- Linie nach unten
G01 X-50 Y-30      <- Linie nach links
G01 X-50 Y20       <- Linie nach oben (geschlossen)
G00 Z5.000000      <- Stift heben, fertig
```

`G21` (mm) und `G90` (absolute Koordinaten) interessieren den Roboter nicht – sie sind «Höflichkeit» gegenüber echten CNC-Maschinen. `Walldraw.ino` arbeitet von Natur aus absolut und in mm.

## 3. Der Weg vom PNG zum G-code mit Inkscape

Wichtigster gedanklicher Schritt: Ein PNG ist eine Pixelrasterung, der Roboter zeichnet aber Linien (Vektoren). Dazwischen muss das PNG vektorisiert werden.

```mermaid
flowchart LR
    A[PNG] -->|"Bitmap nachzeichnen (Potrace)"| B[Vektorpfade SVG]
    B -->|"Gcodetools: Pfad zu Gcode"| C["1.nc Datei"]
    C --> D["TF-Karte FAT32"]
    D --> E["Arduino liest X/Y/Z<br/>rechnet Schnurlaengen"]
    E --> F["2 Schrittmotoren<br/>zeichnen das Bild"]]
```

Schritt für Schritt in Inkscape (Menüführung plattformübergreifend für Inkscape 1.x, lokal installiert auf dem MacBook Air):

1. **Dokument einrichten**: Datei → Dokument-Eigenschaften → Einheiten auf **mm** stellen.
2. **PNG importieren**: Datei → Importieren.
3. **Vektorisieren**: PNG auswählen → Pfad → **Bitmap nachzeichnen** (Umschalt+Alt+B). Modus «Einfarbiger Scan» mit **Helligkeitsschwelle** ist ideal für Logos, Silhouetten und Strichzeichnungen; Schwellwert-Regler + «Aktualisieren» bis die Vorschau passt, dann «Anwenden». Anschliessend das Original-PNG löschen – die neuen Vektorpfade liegen exakt darüber.
4. **Aufräumen**: Pfad → **Vereinfachen** (Strg+L) reduziert überflüssige Knoten – jeder Knoten wird später eine G-code-Zeile und kostet Zeichenzeit. Zusätzlich: Pfad → Objekt zu Pfad (Strg+Umschalt+C), Gruppen lösen (Strg+Umschalt+G).
5. **Physikalische Grösse setzen**: Zeichnung auf die effektive Wandgrösse in mm skalieren (oben in der Werkzeugleiste W/H eingeben).
6. **Orientierungspunkte setzen**: Erweiterungen → **Gcodetools** → Orientierungspunkte → 2-Punkte-Modus, Z-Oberfläche 0, Z-Tiefe −1, Einheiten mm. Punkt 1 = Nullpunkt, in der **Bildmitte** platzieren (= Home-Punkt des Roboters); Punkt 2 typischerweise 100 mm daneben.
7. **Werkzeug definieren**: Erweiterungen → Gcodetools → Werkzeugsammlung → «Default» → Anwenden. Vorschub-Werte im grünen Kasten darf der Polargraph ignorieren (kein F-Wort in der Firmware).
8. **G-code erzeugen**: Pfade auswählen → Erweiterungen → Gcodetools → **Pfad zu Gcode** → im Reiter «Einstellungen» Zielordner und Dateiname → Anwenden → `.ngc`-Datei.
9. **Für den Roboter herrichten**: Datei in **`1.nc`** umbenennen, auf **FAT32-TF-Karte** (vorteilhaft ≤ 4 GB) kopieren.

Gcodetools ist bei Inkscape ab Werk dabei (Erweiterungen → Gcodetools); Projekt: https://github.com/cnc-club/gcodetools

## 4. Wie der Arduino die Datei verarbeitet (Rechenbeispiel)

Die G-code-Koordinaten sind karthesisch (X/Y in mm), die Motoren kennen nur «Schnur auf» und «Schnur ab». Die Firmware übersetzt bei jedem Befehl:

**Schritt 1 – Schnurlängen berechnen (Satz des Pythagoras).** Aus `Pos2StepCnt(x, y)`: `L = Wurzel(dx² + dy²)` zu jedem Aufhängepunkt. Beispiel mit den Default-Werten (Schnurlöcher bei ±500 mm, Höhe 422 mm; Schnur pro Schritt = 35 mm · Pi / 2048 ≈ 0,0537 mm):

| | Home (0|0) | Ziel `G01 X200 Y-100` | Änderung |
|---|---|---|---|
| Schnur links | Wurzel(500² + 422²) ≈ 654.3 mm | Wurzel(700² + 522²) ≈ 873.2 mm | +218.9 mm |
| Schnur rechts | 654.3 mm | Wurzel(300² + 522²) ≈ 602.1 mm | −52.2 mm |

**Schritt 2 – In Schritte umrechnen.** 218.9 mm ÷ 0.0537 mm/Schritt ≈ 4078 Schritte links aufrollen, 52.2 mm ≈ 972 Schritte rechts abrollen.

**Schritt 3 – Gleichzeitig bewegen (Bresenham-Verfahren).** Verhältnis ≈ 4.2 : 1 → der rechte Motor macht ungefähr bei jedem vierten linken Schritt einen Schritt; beide Motoren kommen exakt gleichzeitig an → gerade Linie.

**Schritt 4 – Stiftsteuerung.** Jede Zeile mit `Z > 0` hebt den Stift (Servo auf 86°), `Z <= 0` senkt ihn (46°), sanft in 5°-Schritten.

Einordnung: Im Home-Punkt stehen beide Schnuren bei ca. 654 mm ≈ 12'187 Schritten. Auflösung: gut 5 Hundertstelmillimeter pro Schritt; praktisch begrenzen Schnurdehnung und Stiftreibung das Ergebnis.

## 5. Koordinatensystem und die Datei 1.par

- **(0|0) = Home-Punkt**: Mitte zwischen den Schnurlöchern, beim Default-Aufbau 422 mm darunter.
- **X positiv** = nach rechts, **Y positiv** = nach oben (zu den Motoren hin).
- Zeichenbereich (Default): ca. X in [−500, +500], Y in [−422, +340]; die Firmware verweigert Ziele ausserhalb (Meldung «X-Border exceeded»).

Zeichnung ohne neuen G-code grösser/kleiner oder verschoben ausgeben → Datei **`1.par`** mit drei Zeilen auf die Karte:

```
0.9        <- Skalierungsfaktor (90 % Grösse)
-20        <- Verschiebung X (mm)
-15        <- Verschiebung Y (mm)
```

## 6. Typische Stolpersteine

- **Fotos sind ambitioniert**: Porträts ergeben nach dem Vektorisieren tausende Segmente – der 28BYJ-48 ist langsam, so ein Bild kann Stunden dauern. Einstieg: Strichzeichnungen, Silhouetten, Logos.
- **Reihenfolge im Pfad**: Firmware erwartet X vor Y vor Z in der Zeile – Gcodetools macht das korrekt.
- **Zeichenreihenfolge**: Der Stift springt so, wie die Pfade in Inkscape geordnet sind – Reihenfolge im Ebenendialog beachten.
- **Z-Vorzeichen**: Für den Roboter zählt das Vorzeichen von Z: `Z0.5` hebt, `Z-1` senkt.

## 7. Quellen (Stand 27.10.2026)

- Firmware-Quellcode: https://github.com/Pontifex42/Walldraw/blob/master/UNO/Code/Walldraw/Walldraw.ino
- Original-Firmware und Demo-Programme: https://github.com/shihaipeng03/Walldraw
- Händler-Repo mit Anleitung: https://github.com/MoebiusTech/Wall-Draw-Painting-Robot
- Inkscape Vektorisieren-Tutorial (deutsch): https://inkscape.org/de/doc/tutorials/tracing/tutorial-tracing.html
- Gcodetools: https://github.com/cnc-club/gcodetools
- Gcodetools-Workflow (Orientierungspunkte, Path to Gcode): https://salivity.github.io/inkscape/article/convert-vector-paths-to-g-code-using-inkscape
