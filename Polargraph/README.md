# Polargraph – Wandmal-Roboter (BinHex Wall Drawing Machine)

**Status:** Bausatz am 27.10.2026 bei AliExpress (China) bestellt – wartet auf Lieferung.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 27.10.2026 (zuletzt aktualisiert: 29.10.2026)

Dieses Dokument fasst die Recherche aus dem Vibe-BrainGym (Oktober 2026) zusammen: Produktidentifikation, Funktionsprinzip, Firmware-Herkunft und Vorgehen beim Erstbetrieb.

## Dokumente in diesem Ordner

- `README.md` – Projektübersicht und Recherche-Zusammenfassung (dieses Dokument)
- `G-code-Einfuehrung.md` – Tutorial: G-code-Grundlagen, Workflow PNG → Inkscape → G-code, und wie der Arduino die Datei verarbeitet
- `gcode/gcode_wascher.py` – Python-Skript (Thonny): säubert svg2gcode-Ausgabe für Walldraw – fügt Stift-Befehle (Z) ein, entfernt Kommentare, Zeilennummern, Prüfsummen und Vorschub; optional `--zentrieren`
- `gcode/Schneemann/1.nc` – erste fertige Zeichnung: Schneemann (59 Striche, 237 × 173 mm, um Home zentriert, 16’238 Zeilen)
- `Plan-B-Polargraph-Software.md` – Analyse der Original-Polargraph-Software (Sandy Noble) als zweite Steuerungsoption («Plan B»): Versions-/Alters-Check, Lauf-Umgebungs-Check (MacBook M2/Rosetta, Raspberry Pi 4B), Anpassungs-Checkliste und Entscheidungsbaum

---

## 1. Produkt-Identifikation

- **Beigelegte Anleitung:** BinHex «Robot Kit», Model BR-001 – minimal (Sicherheitshinweise, FAQs, After-Sales; typisch für AliExpress-Kits).
- **Passendes AliExpress-Produkt:** «Draw Wall Painting Robot with Cable Plotter for Arduino Robot DIY Kit Polar Graph with Motor for UNO Programmable Robot Starter» (verkauft u. a. von MOEBIUS Official Store, Byte Technology Store).
- **Preisrahmen:** ca. 50–80 USD/EUR je nach Set (Full set / mit TF-Karte).
- **Robotertyp:** Polargraph (auch Kabelplotter, V-Plotter oder Drawbot genannt) – ein hängender Zeichnroboter für Wandbilder.

## 2. Funktionsprinzip Polargraph

- Zwei Schrittmotoren sitzen oben links und rechts an der Wand; jede Spule trägt eine Schnur.
- An den beiden Schnüren hängt die «Gondel» (Stifthalter); ein kleiner Servo hebt und senkt den Stift.
- Die Stiftposition ergibt sich rein aus den beiden **Schnurlängen** (Satz des Pythagoras) – dieselbe Dreiecks-Geometrie wie GPS-Trilateration, nur 2D mit zwei Bezugspunkten.
- Stärken: riesige Zeichenfläche bei minimaler Mechanik. Schwächen: Genauigkeit Richtung Bildränder geringer, Kalibrierung nötig.
- **Künstlerische Wurzel der Gattung:** [Hektor](https://juerglehni.com/works/hektor) (Jürg Lehni & Uli Franke, 2002) – der an zwei Schnüren hängende Sprühdosen-Plotter, mit dem die maschinengesteuerte Wandkunst bekannt wurde und der die ganze Polargraph-/Drawbot-Szene inspiriert hat.
- **Dazu passend:** [Scratchdisk](https://scratchdisk.com/) – Jürg Lehnis Artikel-Sammlung zu Programmierung, JavaScript, Geometrie und Vektorgrafik (u. a. über Paper.js) – der «Hintergrund-Feed» zum künstlerischen Ursprung.

## 3. Technik des Kits

| Baustein | Funktion |
|---|---|
| Arduino UNO | Steuereinheit, liest G-code autonom von der TF-Karte |
| 2× 28BYJ-48 Schrittmotoren | Spulen die Schnüre auf/ab (über ULN2003-Treiber) |
| SG90-Servo | Stift heben/senken |
| TF-/SD-Karte (FAT32, vorteilhaft ≤ 4 GB) | Speichert Zeichnung als G-code «1.nc», optional «1.par» |
| Holzteile, Schnüre, Gegengewichte | Rahmen, Gondel, Schnurmechanik |

Der Roboter zeichnet **autonom ohne PC**: Firmware liest die Datei «1.nc» von der Karte und wandelt die Koordinaten in Schrittmotorbewegungen um.

## 4. Firmware WallDraw.ino – GitHub-Herkunft

| Repo | Bedeutung |
|---|---|
| https://github.com/WorkTimer/Walldraw | Ursprung (ca. 2019, chinesisch, «墙画机» Wandmalmaschine) |
| https://github.com/shihaipeng03/Walldraw | Hauptversion des Originalautors: 2Steper.ino (Motortest), WallDrawDemo.ino (Geometrie-/Schmetterlingskurven-Test), WallDrawGCode, WalldrawSDCard, Bibliotheken, Anleitungs-PDFs |
| https://github.com/MoebiusTech/Wall-Draw-Painting-Robot | Repo des AliExpress-Händlers (MOEBIUS) mit englischem Guide + «How to paint Einstein on the wall» |
| https://github.com/Pontifex42/Walldraw | **Empfohlen:** deutschsprachige Anleitung «Wandplotter.pdf», verbesserter Code für UNO und ESP32, Stückliste, 3D-Dateien (GPL-2.0) |

### Wichtigste Code-Konstanten (Kalibrierung, aus Pontifex42/Walldraw.ino)

- `STEPS_PER_TURN` = 2048 (28BYJ-48), `SPOOL_DIAMETER` = 35 mm → ca. 0,054 mm Schnur pro Schritt
- `X_SEPARATION` = 1000 mm (Abstand der Schnurlöcher), `Y_TWINEHOLES` = 422 mm
- Stiftwinkel: 86° (oben) / 46° (unten)
- Pins: Motor links 7/8/9/10, Motor rechts 2/3/5/6, Servo A0, SD-ChipSelect 4
- `loop()`: liest optional «1.par» (Resize-Faktor + Offsets), zeichnet «1.nc», zurück zu 0|0

## 5. Workflow: von der Idee zum Wandbild

1. Zeichnung als SVG in Inkscape (MacBook Air) erstellen → mit **svg2gcode** in G-code umwandeln → mit `gcode/gcode_wascher.py` für Walldraw säubern (Datei «1.nc») – Details im Dokument [G-code-Einfuehrung.md](G-code-Einfuehrung.md) und in Abschnitt 5.1.
2. Datei auf FAT32-TF-Karte kopieren; optional «1.par» anlegen (Skalierung + Zentrierung).
3. Maschine aufbauen, Wand-Geometrie ausmessen und Konstanten im Sketch anpassen.
4. Mit WallDrawDemo.ino Maschine testen (ohne SD-Karte), dann erste kleine Testbilder (Quadrat, Kreis, Diagonalen).
5. Zeichnung starten lassen – Fertigmeldung «Drawing finished» im Serial Monitor.

### 5.1 Werkzeugkette SVG → 1.nc (Stand 29.10.2026)

**Pipeline:** Inkscape (SVG) → svg2gcode → gcode_wascher.py → 1.nc auf TF-Karte

| svg2gcode-Einstellung | Empfehlung | Grund |
|---|---|---|
| Tool on / off | `G01 Z-1` / `G01 Z5` | Stift senken/heben – Walldraw: Z > 0 = Stift oben, Z ≤ 0 = Stift unten. Fehlt die Einstellung, fügt `gcode_wascher.py` die Z-Befehle nachträglich ein |
| Circular interpolation | aus | Walldraw kennt keine G02/G03-Bögen, nur Geradensegmente |
| Tolerance | 0.5 mm | Standard 0.002 mm erzeugt Zehntausende Zeilen (Schneemann: 16’130), ohne sichtbaren Gewinn beim Filzstift |
| Zeilennummern / Prüfsummen | aus | Streaming-Protokoll für 3D-Drucker; Walldraw ignoriert sie, die Datei wird nur aufgebläht |
| Kommentare | entfernen | Walldraw liest blind X/Y/Z – ein Kommentar mit diesen Buchstaben (z. B. «layer») würde als Bewegung fehlgelesen |
| Origin | (−Breite/2, −Höhe/2) | Zeichnung um Home zentrieren – alternativ `--zentrieren` im Wasch-Skript |

Beispiel Schneemann: 59 Striche, 237 × 173 mm, nach dem Waschen 16’238 Zeilen (321 KB), Weglänge ca. 6 m (3.9 m zeichnen + 2.1 m Eilgänge).

### 5.2 Universal G-Code Sender – Option für GRBL-basierte Maschinen (Stand 29.10.2026)

[Universal G-Code Sender](https://github.com/winder/Universal-G-Code-Sender) (UGS) – ausgereifter, plattformunabhängiger Desktop-Sender (Java, aktiv gepflegt), der G-code über die serielle Schnittstelle an GRBL-kompatible Firmware streamt (Vorschau, Jogging, DRO).

Einordnung für unser Setup:

- Passt **nicht** zur Walldraw-Firmware des BinHex-Kits – sie liest G-code autonom von der TF-Karte, nicht über USB. Der gängige Weg von UGS führt zu GRBL-basierten Polargraph-Firmwares wie [grbl-polargraph](https://github.com/ramon-umleal/grbl-polargraph) (NEMA17 + A4988/CNC-Shield).
- Ersetzt also nicht den «Plan B» (Polargraph-Controller von Sandy Noble, siehe [Plan-B-Polargraph-Software.md](Plan-B-Polargraph-Software.md)), sondern wäre Teil eines späteren «Plan C» mit anderer Hardware.
- falls einmal eine GRBL-basierte Maschine entsteht: unsere gewaschene G-code-Ausgabe (Z-Befehle, zentriert) wäre direkt weiter verwendbar.

### 5.3 Paper.js – generative Vorlagen aus dem Geiste von Hektor (Stand 29.10.2026)

[Paper.js](https://github.com/paperjs) – etablierte Open-Source-Skriptbibliothek (JavaScript) für Vektorgrafik; hervorgegangen aus Scriptographer, ebenfalls von Jürg Lehni mitbegründet. Damit schliesst sich der Kreis zur künstlerischen Wurzel (Abschnitt 2): dieselbe Handschrift wie hinter Hektor.

Nutzen für unsere Werkzeugkette:

- Mit Paper.js lassen sich **generative SVGs programmatisch erzeugen** (Muster, Geometrie, Typografie, Zufallsstrukturen) – vom Handzeichnen completely unabhängige Kunstquelle.
- Die Ausgabe fliesst direkt in die bestehende Pipeline: **Paper.js → SVG → svg2gcode → gcode_wascher.py → 1.nc**.
- Vertiefende Artikel zu Geometrie/Vektorgrafik aus dieser Ecke: [Scratchdisk](https://scratchdisk.com/).

## 6. Praxistipps aus der Community-Recherche

- Nur **dehnungsarme Schnur** verwenden (geflochtene Dyneema-/HT-Angelschnur) – dehnbare Schnur verzerrt das Bild.
- Kleines **Gegengewicht** an der Gondel hält die Schnüre straff; zu leicht = Pendeln, zu schwer = Motor verliert Schritte (hörbar am Klick-Geräusch).
- Weicher **Filzstift** mit sanfter Auflage – klemmender Stift ist der häufigste Praxiskiller.
- Home-Punkt und Motorabstand sorgfältig ausmessen; die Software kennt nur, was man ihr misst.
- Verkäufer nach vollständigem **englischen Guide + Quellcode** fragen (die beigelegte Anleitung ist minimal).

## 7. Nächste Schritte (nach Lieferung)

1. Teile-Check gegen Stückliste.
2. WallDrawDemo.ino aufspielen (testet Motoren + Servo ohne SD-Karte).
3. Wand-Geometrie ausmessen, eigene Werte in Walldraw.ino eintragen.
4. Erste eigene Zeichnung via Inkscape → 1.nc → Wand.

## 8. Quellen (Stand 27.10.2026, Ergänzungen 29.10.2026)

- Kit-Beschreibung mit 28BYJ/FAT32/1.nc-Details: https://www.sinoning.com/product/drawbot-cable-plotter-wall-painting-robot-for-arduino-with-stepper-motor-servos-diy-maker-project-kit-polargraph/
- AliExpress-Produkt: https://www.aliexpress.com/item/1005006668752734.html
- Polargraph-Grundlagen (Mathematik): https://1c3d.com/projects/build-polargraph-wall-mounted-vertical-drawing-machine
- Sandy Nobles Polargraph (Ursprung der Gattung): https://github.com/euphy/polargraph
- Instructables-Workflow: https://www.instructables.com/Drawing-Robot-Board-Polargraph-Plotter/
- Hektor – künstlerische Inspiration (Jürg Lehni & Uli Franke, 2002): https://juerglehni.com/works/hektor
- Scratchdisk – Jürg Lehnis Artikel zu Vektorgrafik/Programmierung: https://scratchdisk.com/
- Universal G-Code Sender (GRBL-Sender, Option «Plan C»): https://github.com/winder/Universal-G-Code-Sender
- Paper.js – Vektorgrafik-Bibliothek (generative SVG-Vorlagen): https://github.com/paperjs
