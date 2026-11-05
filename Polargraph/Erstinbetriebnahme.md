# Erstinbetriebnahme – Analyse der Kit-Dokumentation (Walldraw_en) und Inbetriebnahme-Plan

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 05.11.2026

**Status:** Bausatz am 05.11.2026 aus China geliefert. Die Anbieter-Dokumentation liegt im Drive-Ordner [Polargraph/Walldraw_en](https://drive.google.com/drive/folders/12AsbQnxWdhv3H4KK_Xjyotc1WO6R82qt) und wurde am 05.11.2026 vollständig ausgewertet. Dieses Dokument fasst die Befunde zusammen und ersetzt die «Nächste Schritte»-Planung aus der README durch einen konkret am Kit messbaren Ablauf.

---

## 1. Inhalt des Dokumentations-Pakets

| Pfad (Drive: Polargraph/Walldraw_en) | Inhalt | Nutzen für uns |
|---|---|---|
| Wall Drawing Machine installation instructions.pdf | Montage, Verkabelung, Parameter-Erklärung, FAQ | **Zentrales Dokument** für Aufbau und Kalibrierung |
| Frequently asked questions.docx | FAQ-Ergänzung (Geschwindigkeit, Genauigkeit, Fehlersuche) | Praxiswerte und Troubleshooting |
| How to draw Einstein on the wall.pdf | Theorie + Bitmap-Workflow | Bekannt (identisch mit MoebiusTech-Guide) |
| Walldraw/Walldraw.ino | **Produktiv-Firmware** (liest G-code von TF-Karte, zeichnet «1.nc») | Massgeblich für Pins/Konstanten |
| Walldraw/WallDrawGCode_instructions/ | Beta-Firmware WallDrawGCODE (G-code über USB-Seriell) + fertig kompiliertes **HEX** + **XLoader** (Flashen ohne Arduino IDE) | Alternative Betriebsart (Experiment) |
| WallDrawDemo/WallDrawDemo.ino | Geometrie-Demo (Boxen, Kreise, Herz-Kurve, Schmetterlings-Kurve) | Maschinentest nach Montage |
| 2Steper/2Steper.ino | Reiner Motortest (AccelStepper, zeichnet Zykloidenmuster) | Erster Funktionstest |
| NC/ | **17 fertige Demo-Zeichnungen** (.nc) mit Grössenangaben im Dateinamen | Sofort zeichenfertige Tests |
| Lib/ | Bibliotheken TinyStepper_28BYJ_48, SD, AccelStepper + Readme | Für Arduino-IDE-Compilation |
| 1.jpg, 2.jpg | Fotos (Verkabelung) | Anschauung |

## 2. Kritische Abweichungen: Kit-Firmware vs. unsere bisherigen Annahmen

Bislang richteten wir uns nach Pontifex42/Walldraw.ino. Die **mitgelieferte** Firmware weicht davon ab – und selbst der Hersteller benutzt in seinen drei Sketches unterschiedliche Werte. Alle genannten Werte sind also Beispiele; massgeblich ist die eigene Vermessung.

| Parameter | Pontifex42 (alt) | Kit Walldraw.ino | Kit WallDrawDemo.ino | Kit WallDrawGCODE (Beta) |
|---|---|---|---|---|
| `X_SEPARATION` | 1000 | **507** | 507 | 505 |
| Y-Parameter | `Y_TWINEHOLES` 422 | `LIMYMIN` 440 / `LIMYMAX` −440 | 430 / −430 | 300 / −300 |
| Stiftwinkel oben/unten | 86° / 46° | **60° / 95°** | 70° / 85° | – |

**Bestätigt (identisch mit unserer Recherche):**

- Pins: Motor M1 (links) 7/8/9/10, Motor M2 (rechts) 2/3/5/6, Servo A0 (nur mit SD-Reader; ohne Karte wäre 13 möglich, ist dann aber von SCK belegt), SD-ChipSelect 4 (MOSI 11, MISO 12, SCK 13)
- `STEPS_PER_TURN` 2048, `SPOOL_DIAMETER` 35 mm → **TPS = 0,0537 mm/Schritt** (in der beigelegten TinyStepper-Bibliothek verifiziert: 2048 Schritte/Umdrehung; die FAQ-Angabe «0,027 mm Auflösung» ist der theoretische HalbSchritt-Wert, nicht die effektive Firmware-Auflösung)
- Z-Konvention: Z > 0 = Stift heben, Z ≤ 0 = senken; Zeilen werden GROSS-geschrieben (`toUpperCase`) – Kommentare mit X/Y/Z-Buchstaben sind gefährlich (bestätigt, unser gcode_wascher regelt das)
- Zeilen ohne X **und** Y werden als Bewegung ignoriert (reine Z-Zeilen wirken trotzdem) – deshalb funktionieren reine Stift-Befehle wie `G01 Z5` problemlos
- Nach dem Zeichnen endet `loop()` in einer Endlosschleife → **Maschine per Reset neu starten** für die nächste Zeichnung

**Neu präzisiert (Installations-PDF):**

- `X_SEPARATION` = Abstand der beiden **Seil-Durchtrittsösen** an den Halterungen – **nicht** der Spulenabstand!
- Y-Ursprung: Die **Ruheposition des Stifts beim Einschalten** ist 0|0. `LIMYMIN` = vertikaler Abstand von dieser Position zur Ösenlinie (positiv, nach oben). Empfehlung Hersteller: Stift beim Einschalten in die Mitte des Blatts legen und `LIMYMIN` so gross machen wie der gewünschte Zeichenbereich nach unten (`LIMYMAX` = −LIMYMIN)
- Zeichenfläche soll **mind. 2× so gross** sein wie das Bild (kleinere Bilder = weniger Verzerrung; optimale Zone: mittleres Band unterhalb der Ösenlinie)
- Servo-Hub nur **5–10°** – grössere Bewegungen erzeugen Vibration, verschlechtern die Genauigkeit und verlangsamen den Ablauf

## 3. Montage-Highlights (Installations-PDF)

- Schrauben zuerst sortieren: 12 grosse Flachkopfschrauben + 12 Kupferabstandsposten fürs Chassis; UNO und Motor-Treiberplatinen auf die Posten (Motherboard-Schrauben).
- **SD/TF-Reader kleben statt schrauben** (Revisions-Hinweis des Herstellers: neuere Kits ohne Schraubbefestigung).
- Spulen: Schnur in den Schlitz der Spule einhängen; **links im Uhrzeigersinn, rechts gegen den Uhrzeigersinn** wickeln.
- Seil-Führungshülse (verringert Reibung) in die Öse der Halterplatte einhängen; die Hülse sitzt in der Öse, die Schnur zum Stift.
- Stifthalter: Drehachse **nicht fest** anziehen – der Halter muss frei schwenken können; Schwerpunkt mittig (mitgelieferten Servo in Fotoposition einbauen).
- Servo **niemals von Hand verdrehen** (Beschädigungsgefahr) – stattdessen Schwungrad abnehmen, Winkel setzen, wieder aufstecken.
- Stift so fixieren, dass die Spitze das Papier **gerade eben berührt**; nicht halben Stift ausragen lassen.
- Gegengewicht-Halter hinten nur bei Stiften anderer Bauart nötig.

## 4. Verkabelung

- Das mitgelieferte **Shield** («extended version») wird auf den UNO gesteckt und wirkt als Klemmleiste: jede UNO-Position hat S (Signal), V/VCC/5V (+) und G/GND (−); V und G sind nicht nummeriert, beliebig belegbar.
- Servo: braun = GND, rot = VCC, gelb = Signal → **A0** (bei SD-Betrieb).
- Schrittmotor-Treiberboards: In1–In4 → einerseits 2/3/5/6, andererseits 7/8/9/10 (Gemäss Firmware-Kommentar: M1 links = 7/8/9/10, M2 rechts = 2/3/5/6; die PDF-Nummerierung nennt es umgekehrt – bei seitenverkehrtem Bild liefern die `M1/M2_REEL`-Vorzeichen oder getauschte Motor-Anschlüsse die Korrektur).
- SD/TF-Reader-Modul: CS→4, MOSI→11, MISO→12, SCK→13, VCC→5V, GND→−; 3,3 V bleibt unbenutzt.
- **Kartenkompatibilität:** FAT32 zwingend, kein NTFS/exFAT, kein SDXC > 32 GB – «alte kleine Karten» funktionieren am besten (≤ 16 GB empfohlen). TF-Kartenleser-Modul dem TF→SD-Adapter vorziehen (Adapter machen teils Probleme).
- **Mac-Falle (FAQ!):** Vom Mac kopierte Dateien können trotz korrektem Namen nicht gelesen werden – AppleDouble-Dateien (`._1.nc`, `.DS_Store`) löschen und die Datei notfalls am Arduino-PC/kompatiblen System neu benennen.

## 5. Inbetriebnahme-Reihenfolge (gemäss Hersteller-Doku)

1. **Teile-Check** gegen die Stückliste (Schraubensorten unterscheiden!).
2. **2Steper.ino** flashen: reiner Motortest, zeichnet ein Zykloidenmuster (mit `stp1`/`stp2` lässt sich das Muster verändern). Erster Lebenszeichen-Check der Mechanik.
3. **WallDrawDemo.ino** flashen – **ohne Stift** (Seilhülse nur in den Halter hängen), Gondel leerfahren lassen und prüfen, ob der Bereich aufs Papier passt. Orientierungs-Check per Demo-Muster: Neunerkasterl oben, Herz unten links, Schmetterling unten rechts (`demo1`; `demo2` = zufällige Bogen-Kritzeleien, auskommentiert).
4. **Kalibrieren** in Walldraw.ino: `X_SEPARATION` (Ösenabstand ausmessen), `LIMYMIN` (vertikaler Abstand Ruheposition→Ösenlinie), `PEN_UP_ANGLE`/`PEN_DOWN_ANGLE` (Hub 5–10°).
5. **Erste Zeichnung:** Demo-Datei aus dem NC-Ordner nehmen, auf der TF-Karte in **1.nc** umbenennen (Dateiname muss exakt zur Firmware passen – sonst liest die Maschine nichts!), zeichnen lassen, danach Reset für die nächste.

## 6. Demo-Zeichnungen im NC-Ordner (alle zu 1.nc umbenennen)

Grundsatz aus NC/instructions.txt: Dateiname = reale Zeichengrösse; erst klein testen, dann grosse/komplexe Bilder. Zeichenfläche ≥ 2× Bildgrössse wählen.

| Datei | Grösse | Bemerkung |
|---|---|---|
| Geometry 200×100 mm.nc | klein | **Idealer erster Test** (geprüft: Z-Befehle korrekt nach Z>0-heben/Z≤0-senken, keine G2/G3-Bögen, 5233 Zeilen) |
| Fibonacci spiral 150×100 mm.nc | klein | 254 Zeilen, sehr schnell |
| Arduino 50×35 mm small.nc / arduino 250×130 mm.nc | klein/mittel | |
| Mona Lisa 150 line A4 / 600 line A4 | A4 | 600-line = deutlich länger |
| Wall-E 220×220, Iron Man 350×350, Sail battleship 200×200 | mittel | |
| HarryPotter A4, Dakar A4 | A4 | |
| Walt Disney A3, Coca-Cola A2 | gross | erst nach erfolgreichen Klein-Tests |

**Zeitbedarf (FAQ):** Stiftgeschwindigkeit 9–27 mm/s (Mittel 13,7 mm/s). Einfaches A4 ≈ 10 min, komplexes A4 > 1 h, A0 ≈ 5,5 h. Zum Vergleich: unser Schneemann (ca. 6 m Weg) ≈ 7–8 min.

## 7. WallDrawGCODE – die USB-Variante (Beta)

Im Paket liegt eine zweite Firmware-Variante: **WallDrawGCODE** liest G-code nicht von der Karte, sondern **über die serielle Schnittstelle (115200 Baud)** – die Maschine wäre also PC-gesteuert betreibbar (gleiche Richtung wie Universal G-Code Sender, Abschnitt 5.2 der README). Der Hersteller liefert sie fertig kompiliert als **HEX-Datei** (WallDrawGCode.v210428a.hex) plus **XLoader** (Flash-Tool ohne Arduino IDE).

- Defaults: `X_SEPARATION` 505, Y ±300, sonst gleiche Physik (TPS 0,0537 mm).
- Der Hersteller selbst bezeichnet sie als **Beta** («This program is a beta version»).
- Einordnung für uns: für den Regelbetrieb bei **Plan A (SD-Karte)** nicht nötig; interessant als Experiment für PC-gesteuertes Zeichnen ohne TF-Karten-Shuttle.

## 8. Fehlerbehebung (FAQ-Kurzfassung)

| Symptom | Massnahme |
|---|---|
| Bild spiegelverkehrt / gedreht / 90° versetzt | Vorzeichen von `M1/M2_REEL_IN/OUT` ändern; linke/rechte Motorverkabelung tauschen; `LIMX/LIMY`-Vorzeichen; bei 90°-Drehung Vergleichszeichen in `moveto()` |
| Starke Verzerrung | Meist falsche Startposition: Stift beim Einschalten nicht dort, wo die Parameter es annehmen (0|0). `LIMYMIN` nachmessen, Stift mittig platzieren |
| `initialization SD failed!` (Serial Monitor) | Karte nicht FAT32/zu gross, Reader-Verkabelung, Dateiname nicht exakt «1.nc» (Mac-Problem: neu kopieren umbenennen) |
| Karte ok, aber nichts bewegt sich | G-code-Format inkompatibel (z. B. nur M3/S0-Laserbefehle statt Z-Werten) – Stiftbefehle durch `G01 Z1` (heben) / `G01 Z0` (senken) ersetzen |
| Motoren brummen/rütteln nur | Verkabelung/Stromversorgung prüfen (Schrittfolge nicht ändern!) |
| Spulen drehen «wild», Stift hängt an der Halterung | G-code-Koordinaten grösser als die Zeichenfläche (z. B. X9999) – Werte prüfen, Bildfläche ≥ 2× Bild |
| Stift hebt nicht / hebt zu weit | Stift wenig ausragen lassen; Schwungrad neu positionieren; Hub auf 5–10° begrenzen |

## 9. Checkliste Erstinbetriebnahme

- [ ] Teile gegen Stückliste komplett, Schraubensorten sortiert
- [ ] Chassis montiert (12 Flachkopfschrauben + Kupferposten), SD-Reader **geklebt**
- [ ] Shield aufgesteckt, Verkabelung gemäss Abschnitt 4 (Servo A0, SD CS 4)
- [ ] 2Steper.ino geflasht – beide Motoren drehen, Zykloidenmuster sichtbar
- [ ] WallDrawDemo.ino geflasht – Leerfahrt ohne Stift, Bereich passt aufs Blatt
- [ ] Orientierung stimmt (Neunerkasterl oben / Herz unten links / Schmetterling unten rechts)
- [ ] `X_SEPARATION` gemessen (Ösenabstand!) und eingetragen
- [ ] `LIMYMIN` gemessen (vertikaler Abstand Ruheposition→Ösenlinie) und eingetragen
- [ ] Stiftwinkel kalibriert (Hub nur 5–10°, Stiftspitze berührt Papier gerade)
- [ ] TF-Karte FAT32 (≤ 16 GB), Demo-Datei als 1.nc umbenannt (Mac: ~._~-Dateien entfernt)
- [ ] Erste Zeichnung: Geometry 200×100 mm.nc auf die Wand/Papier
- [ ] Danach: eigene Zeichnungen via Inkscape → svg2gcode → gcode_wascher.py → 1.nc

## 10. Quellen (Stand 05.11.2026)

- Kit-Dokumentation des Anbieters (Drive): https://drive.google.com/drive/folders/12AsbQnxWdhv3H4KK_Xjyotc1WO6R82qt
- Original-Repo des Firmware-Autors: https://github.com/shihaipeng03/Walldraw
- Prinzip-Artikel des Herstellers (Zhihu): https://zhuanlan.zhihu.com/p/71602189
- «How to draw Einstein on the wall» (auch als PDF im Paket): https://github.com/MoebiusTech/Wall-Draw-Painting-Robot
- Unsere bisherige Recherche: [README.md](README.md) (Abschnitte 3–5), [G-code-Einfuehrung.md](G-code-Einfuehrung.md), [ANLEITUNG-gcode-wascher.md](gcode/ANLEITUNG-gcode-wascher.md)
