# Anleitung: G-code selbst waschen mit gcode_wascher.py (ohne Vibe)

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 30.10.2026

Ziel: Du kommst allein vom svg2gcode-Output bis zur fertigen TF-Karte – kein Vibe, kein Terminal-Zwang, nur Thonny und dieses Skript.

## 1. Worum es geht

Der Wandmal-Roboter (Firmware WallDraw.ino) ist empfindlich beim Lesen seines G-codes:

| Verträgt die Firmware | Verträgt sie NICHT |
|---|---|
| Wörter X, Y und Z pro Zeile | alles andere (F-Wörter, M-Befehle, Kommentare) |
| Z > 0 = Stift oben, Z ≤ 0 = Stift unten | Stift-Befehle, wenn sie fehlen: Verbindungslinien im Bild |
| kurze, saubere Zeilen | Zeilennummern/Prüfsummen (Datei-Aufblähung), Kommentare mit X/Y-Buchstaben (Fehlbewegungen!) |

Das Skript `gcode_wascher.py` (Version 2) erledigt alle Aufräumarbeiten automatisch und fragt dich im Dialog nach den nötigen Angaben.

## 2. Vorbereitung (einmalig)

1. [Thonny](https://thonny.org/) installieren (falls noch nicht vorhanden) – oder ein anderes Python 3.
2. Einen Ordner für die Zeichnerei anlegen, z. B. `polargraph-gcode`, und `gcode_wascher.py` hineinkopieren.
3. Empfehlung: die G-code-Dateien von svg2gcode gleich in denselben Ordner legen – dann reicht im Dialog der bloße Dateiname.

## 3. Schnellstart in Thonny (der Normalfall)

1. Thonny öffnen → `gcode_wascher.py` öffnen (Datei → Öffnen …).
2. Grünen Run-Pfeil drücken (oder Taste F5).
3. Das Skript stellt unten im «Shell»-Fenster drei Fragen – einfach eintippen und mit Enter bestätigen (leere Eingabe = Vorschlag in Klammern):

```
============================================================
 gcode_wascher v2.0 - Reinigung für den Walldraw-Polargraphen
============================================================
Pfad zur G-code-Datei (z. B. schneemann.gcode): schneemann.gcode
Zieldatei [1.nc]: 1.nc
Zeichnung um Home (0|0) zentrieren? (j/n) [j]: j

Fertig! Statistik:
  Eingabe       : schneemann.gcode
  Ausgabe       : 1.nc (16238 Zeilen)
  Striche       : 59 (dazwischen f
ährt der Stift hoch)
  Zentriert     : ja - Bildmitte liegt auf Home (0|0)
  Zeichnung     : 237 x 173 mm
  Weglänge      : 6.0 m
  Zeit ca.      : 4 min (bei 25 mm/s; real eher mehr)

Nächster Schritt: 1.nc auf die FAT32-TF-Karte kopieren - loszeichnen!
```

4. Die fertige `1.nc` liegt im selben Ordner wie das Skript (bei relativen Pfadangaben: im Arbeitsverzeichnis).
5. `1.nc` auf die TF-Karte (FAT32, vorteilhaft ≤ 4 GB) kopieren – fertig.

**Merkregel:** Einfach starten → drei Fragen beantworten → kurz im Viewer kontrollieren → Datei auf die Karte.

## 4. Bedienung im Terminal (optional, für Schnelltipper)

```bash
# Interaktiv (gleiche Fragen wie in Thonny):
python3 gcode_wascher.py

# Mit Angaben (keine Fragen):
python3 gcode_wascher.py schneemann.gcode 1.nc

# Ohne Zentrierung (Koordinaten bleiben, wie sie sind):
python3 gcode_wascher.py schneemann.gcode 1.nc --kein-zentrieren
```

Tipp macOS: Die G-code-Datei aus dem Finder ins Terminal-Fenster ziehen fügt automatisch den korrekten Pfad ein – ratsam bei Dateinamen mit Leerzeichen.

## 5. Was das Skript Schritt für Schritt tut

| Schritt | Massnahme | Warum |
|---|---|---|
| 1 | Kommentare (`;…`) löschen | Walldraw liest blind X/Y/Z – ein Kommentar mit diesen Buchstaben wird als Bewegung fehlgelesen |
| 2 | Zeilennummern (`N123`) + Prüfsummen (`*45`) löschen | 3D-Drucker-Streaming-Protokoll, unnötig; Datei wird kleiner |
| 3 | Vorschub (`F300`) löschen | Firmware ignoriert ihn sowieso |
| 4 | Alte Stift-Z-Zeilen löschen und neu aufbauen | macht das Skript wiederholbar («idempotent»): bereits gewaschene Dateien dürfen erneut gewaschen werden |
| 5 | `G01 Z5` vor jedem Eilgang (G0), `G01 Z-1` vor dem ersten Strich danach, am Dateiende heben | sonst zieht der Stift Verbindungslinien durchs Bild |
| 6 | Standardmässig: alle X/Y um die Bildmitte verschieben (auf Home 0|0) | Zeichnung erscheint mittig unter der Gondel; abschaltbar mit `--kein-zentrieren` bzw. «n» im Dialog |
| 7 | Statistik + Zeit-Schätzung ausgeben | Kontrolle vor dem Zeichnen |


## 6. Schon beim Konvertieren richtige Einstellungen (svg2gcode-Web-UI)

Das Skript repariert alles – aber sauber konvertiert ist die Datei kleiner und schöner (Details: README Abschnitt 5.1):

- **Tool on/off**: `G01 Z-1` / `G01 Z5`
- **Line numbers + checksums**: abwählen
- **Tolerance**: 0.5 (statt Standard 0.002)
- **Circular interpolation**: aus (sonst warnt das Skript bei G2/G3-Bögen)

## 7. Fehlerbehebung

| Symptom | Ursache & Lösung |
|---|---|
| «Datei nicht gefunden» | Pfad prüfen. Einfachster Fix: G-code-Datei in denselben Ordner wie das Skript legen und nur den Dateinamen tippen (im Terminal: Datei ins Fenster ziehen) |
| «keine X/Y-Koordinaten gefunden» | Das ist kein G-code-File – z. B. ein SVG oder ein Bild. Erst mit svg2gcode konvertieren |
| WARNUNG «G2/G3-Bogenzeilen» | svg2gcode mit «Circular interpolation: aus» neu konvertieren – Walldraw kann keine Bögen |
| Zeichnung steht auf dem Kopf | Y-Achsen-Richtung der Konvertierung. Skript um eine Spiegel-Option erweitern oder in svg2gcode die Y-Achse drehen (bei erstem Testbild kontrollieren) |
| Zeichnung zu klein/gross | Mit `--kein-zentrieren` waschen und die fertige 1.nc an die Maschinengrösse anpassen: entweder in svg2gcode (Origin/Massstab) oder über die Datei «1.par» auf der TF-Karte (Resize-Faktor) |
| Riesige Datei (Zehntausende Zeilen) | tolerance in svg2gcode auf 0.5 erhöhen und neu konvertieren |

## 8. Resultat kontrollieren, bevor es auf die Karte geht

Ein G-code-Viewer zeichnet den Fahrweg am Bildschirm nach – so siehst du in zehn Sekunden, ob die Datei wirklich stimmt. Empfehlung: **NC Viewer** (https://ncviewer.com/, kostenlos, läuft im Browser, keine Installation).

So gehst du vor:
1. https://ncviewer.com/ im Browser öffnen.
2. Die gewaschene Datei (z. B. `1.nc`) per Drag & Drop hineinziehen oder den Inhalt hineinkopieren.
3. Kontrollieren – siehe Checkliste unten.

Checkliste im Viewer:
- Zeichnung vollständig – alle Striche sichtbar (Anzahl muss zur Skript-Statistik «Striche» passen).
- KEINE Verbindungslinien zwischen den Pfaden – das wäre das klassische Symptom fehlender Stift-Befehle; nach dem Waschen darf das nicht mehr vorkommen.
- Zeichnung liegt um den Nullpunkt (Home 0|0) herum, nicht in einer Ecke.
- Massstab plausibel: Grösse im Viewer entspricht der Skript-Statistik (z. B. «237 x 173 mm»).

Gut zu wissen:
- Die Z-Werte zeigt der Viewer als Höhe: Stift hoch (`G01 Z5`) = Fahrt in der Luft, Stift runter (`G01 Z-1`) = zeichnen – in der 3D-Ansicht gut sichtbar.
- Der Viewer ist ein Online-Dienst: die Datei wird an einen fremden Server übertragen. Für unsere Zeichnungen unkritisch – wer das vermeiden will, nutzt die Offline-Alternative.
- Offline-Alternative ohne Viewer: Datei in einem Texteditor öffnen und das Muster prüfen: Anfang `G21`/`G90`, dann `G0 …` (Eilgang), `G01 Z-1`, gefolgt von `G1`-Zeilen; am Ende `G01 Z5`. Mit der Suchfunktion zählen: «G01 Z-1» muss der Strich-Anzahl der Statistik entsprechen.
- Bei sehr grossen Dateien (Zehntausende Zeilen) braucht der Viewer etwas Geduld – dann lieber die svg2gcode-Tolerance erhöhen (Abschnitt 6) und neu konvertieren.

## 9. Checkliste vor dem Zeichnen

1. `1.nc` liegt vor (vom Wasch-Skript, Statistik sah plausibel aus)
2. Kontrollblick im G-code-Viewer bestanden: Zeichnung komplett, keine Verbindungslinien, um Home zentriert (Abschnitt 8)
3. TF-Karte ist FAT32-formatiert (vorteilhaft ≤ 4 GB)
4. Datei heisst auf der Karte exakt `1.nc` (klein geschrieben, kein «.txt»-Anhang)
5. Stift aufgesetzt, Home-Punkt angefahren – und los.

Fragen zur Firmware selbst: siehe [G-code-Einfuehrung.md](../G-code-Einfuehrung.md) und [README.md](../README.md) in diesem Ordner.
