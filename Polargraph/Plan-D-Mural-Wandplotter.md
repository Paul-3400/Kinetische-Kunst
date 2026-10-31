# Plan D – Mural: ESP32-Wandplotter als Nachfolge-Build

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 31.10.2026

**Status:** Recherche- und Bewertungsdokument. Mural ist als möglicher **Nachfolge-Build** nach Plan A (BinHex-Kit, Walldraw) vorgemerkt. Kein Baubeschluss – die Entscheidung fällt nach den ersten Erfahrungen mit dem Kit.

---

## 1. Kurzportrait

| Eigenschaft | Wert |
|---|---|
| Projekt | **Mural** von Nik Ivanov (GitHub: [nikivanov/mural](https://github.com/nikivanov/mural), Website: [getmural.me](https://getmural.me)) |
| Typ | Kabelgesteuerter Wandplotter (Polargraph-Gattung), Wagen hängt an zwei GT2-Zahngurten |
| Kernidee | Die Schrittmotoren sitzen **im Wagen** und spulen die Gurte ein/aus; Steuerung komplett über **Browser** (WiFi) – kein PC-Programm, keine SD-Karte |
| Kosten | ca. 60 USD Bauteile (BOM) + 3D-Druck; total unter 100 USD |
| Reifegrad | Aktiv entwickelt: 232 Commits, letzter Commit 05.01.2026 (Devcontainer-Support); 298 Stars, 75 Forks |
| Doku | BOM mit Referenzfotos, STL-Dateien, Schritt-für-Schritt-Montagevideo (v1.0), Update-Video (v1.1), Kinematik-Dokument, Discord-Community |
| Lizenz | **CC BY-NC 4.0** (Creative Commons, nicht-kommerziell) |
| Zeichnung | Waschbare Filzstifte (Crayola) – Wand wird wiederholt nutzbar |

## 2. Einordnung in die Plan-Landschaft

| Plan | Inhalt | Status/Bewertung |
|---|---|---|
| **A** | BinHex-Kit mit Walldraw-Firmware (UNO, 28BYJ-48, SD-Karte) | Bausatz bestellt, in Umsetzung – **bleibt der Einstieg** |
| **B** | Original-Polargraph-Software (Sandy Noble, Processing 2.2.1) | Dokumentiert ([Plan-B-Polargraph-Software.md](Plan-B-Polargraph-Software.md)); Legacy-Software, nur Nostalgie-Option |
| **C** | GRBL-basierte Polargraph-Firmwares (z. B. grbl-polargraph) mit Universal G-Code Sender | Theoretische Option, andere Hardware nötig |
| **D** | **Mural** (ESP32, NEMA 17, GT2-Gurt, Browser-Steuerung) | Dieses Dokument – technisch überlegener Nachfolge-Build, wenn Plan A Spass macht und die Kit-Grenzen reizen |

**Wichtig:** Mural ist kein Software-Ersatz für Plan A – die Hardware ist grundlegend anders (ESP32 statt UNO, NEMA 17 statt 28BYJ-48, Zahngurt statt Schnur). Die Firmware lässt sich **nicht** auf das Kit portieren.

## 3. Funktionsprinzip

- Zwei Pins (Reissbrettstifte o. ä.) oben an der Wand, Abstand frei wählbar (typisch 1000 mm).
- Der 3D-gedruckte Wagen hängt an **GT2-Zahngurten** (2 mm Teilung, 6 mm Breite), die an den Pins fixieren.
- **Umgekehrte Architektur** gegenüber dem BinHex-Kit: bei Mural sitzen beide NEMA-17-Motoren **im Wagen** und spulen die Gurte auf/ab; beim Kit hängen die Motoren oben und der leichte Gondel hängt an Schnüren. Konsequenz: Mural trägt ca. 400 g Motormasse mit sich – deshalb die aufwendige Kinematik (Abschnitt 5).
- MG90s-Servo (Metallzahnrad) hebt/senkt den Stift.
- Bedienung: ESP32 spannt einen WiFi-Hotspot bzw. joint ins Heimnetz; im Browser SVG hochladen, Parameter setzen, zeichnen starten. OLED-Display zeigt Status und IP-Adresse.
- Zeichnungsfläche: **60 % des Pin-Abstands** nutzbar (bei 1000 mm Pins also 600 mm breit); oben und an den Seiten je 20 % Rand automatisch.

## 4. Hardware (Bill of Materials)

Alle Teile über Amazon/AliExpress/eBay erhältlich; Preise: günstigste AliExpress-Funde ([BOM.md](https://github.com/nikivanov/mural/blob/main/BOM.md)).

| Bauteil | Preis (USD) | Bemerkung |
|---|---|---|
| NodeMCU ESP32 (ESP-WROOM-32, 30 Pins) | 4 | Hauptcontroller, WiFi, Webserver |
| 2× NEMA 17 Pancake-Schrittmotoren (STEPPERONLINE) | 18 | Im Wagen eingebaut |
| 2× Treiber-Erweiterungsplatinen | 2 | |
| 2× BigTreeTech TMC2209-Treiber | 14 | Mikrostepping, leise |
| 2× GT2-Riemenscheibe, 20 Zähne, 5 mm Bohrung | 2 | **Exakte Masse kritisch** (12,69 mm Teilkreis) |
| GT2-Zahngurt, 2 mm Teilung, 6 mm Breite | 6 | |
| MG90s-Servo, Metallzahnrad | 2 | Stift heben/senken |
| USB-C-PD-Trigger-Modul | 1 | Löst 12 V aus dem PD-Netzteil |
| LM2596-Abwandler (Step-down) | 1 | 12 V → 5 V |
| 30-W-USB-C-PD-Netzteil (12 V) | 3 | |
| USB-C-auf-USB-C-Kabel (3 m) | 1 | |
| Breadboard-Jumper (M-F, F-F, 10/20 cm) | 2 | Verdrahtung |
| M3-Schraubenset (6/8/12/25 mm) | 2 | |
| Stiftleisten 2,54 mm | 1 | |
| Gewindeeinsätze M3 | 1 | Optional (einer für den Stift) |
| Daumenschraube M3, 12 mm | 1 | Optional |
| 10-cm-Schrittmotor-Kabel | 2 | |
| **Summe** | **ca. 60** | Ohne 3D-Druck |

**Stromversorgung:** Ein einziges USB-C-PD-Netzteil liefert 12 V für die Motoren; ein LM2596 macht 5 V für ESP32/Servo/OLED. Eleganter als die Batterie-/Netzteil-Lösungen vieler anderer Plotters.

**3D-Druck nötig:** Das komplette Gehäuse (Wagen, Rollenhalter, Stiftlift) ist 3D-gedruckt; STL-Dateien liegen im Repo (Ordner `STLs/`, inkl. 3MF-Update). Ohne eigenen Drucker: Druckdienste (z. B. PCBWay, craftcloud) oder Bekannte – kalkuliert zusätzlich ca. 20–40 USD ein.

## 5. Das kinematische Modell – das Herzstück ⭐

Der entscheidende Qualitätsunterschied zu Walldraw, Polargraph und den meisten Hobby-Plotters liegt in der Bewegungsrechnung. ([KinematicModel.md](https://github.com/nikivanov/mural/blob/main/KinematicModel.md), implementiert in `movement.cpp`, Funktion `getBeltLengths`.)

**Die einfache Welt (Plan A):** Schnurlänge = √(x² + y²) – reine Dreiecksgeometrie nach Pythagoras. Vernachlässigt wird alles andere: Kippung des Wagens, Dehnung des Zugmittels, Rollen-Geometrie.

**Die Mural-Welt (Physik-Modell):**

1. **Neigungswinkel γ:** Der Wagen kippt zur Bildmitte, je näher er einem Rand kommt. Mural modelliert den Wagen als starren Körper mit Schwerpunkt und Pen als separate Punkte.
2. **Kräfte:** Die Gurtkräfte F_L/F_R ergeben sich mit dem Sinussatz aus der Schwerkraft F_G – abhängig von den Gurtwinkeln φ_L/φ_R.
3. **Drehmoment-Gleichgewicht:** Gesucht wird der Winkel γ, bei dem die Drehmomente (Gurtkräfte an den Tangentenpunkten, Gravitation am Schwerpunkt) sich exakt aufheben. Die Firmware löst das numerisch-iterativ bis zur Konvergenz.
4. **Tangentenpunkte:** Der Gurt tangiert die Riemenscheibe (45°-Annahme), greift also nicht im Rollenzentrum an. Korrekturwert q = d_Pulley/(2·√2) = 4,49 mm bei 12,69 mm Scheibe.
5. **Dehnungskorrektur:** Die Gurtlänge wird unter Last korrigiert – Gurte dehnen sich messbar (Dilatation).
6. **3D-Geometrie:** Der Abstand Rolle–Wand (die Scheiben stehen von der Wand ab) fliessen in die effektive Gurtlänge ein.

Ergebnis laut Projekt: Positionierung mit **Submillimeter-Präzision** (Projektangabe) und Zeichnungen ohne sichtbare Schieflage oder Verzerrung, auch an grossen Bildern (bestätigt in der Hackaday-Besprechung). **Konfidenz der Einordnung: hoch** – das Modell ist vollständig dokumentiert und im Code nachvollziehbar; die Präzisionsangabe selbst ist eine Projektbehauptung (Konfidenz: mittel). Der Autor selbst schreibt, die Genauigkeit sei noch verbesserbar (Circuit Digest) – ehrlich und typisch für ein lebendes Projekt.

**Lernwert für Plan A:** Die Ideen der Neigungs- und Dehnungskorrektur lassen sich konzeptionell auf jede Polargraph-Firmware übertragen. Beim BinHex-Kit bleibt der Gewinn aber begrenzt: 28BYJ-48 in Vollschritt (0,054 mm/Schritt Auflösung) und dehnbare Schnur begrenzen die erzielbare Genauigkeit stärker als die Mathematik dahinter (Konfidenz: mittel).

## 6. Software & Bedienung

**Firmware (ESP32, Arduino-Framework, [PlatformIO](https://github.com/nikivanov/mural/blob/main/platformio.ini)):**

| Baustein | Funktion |
|---|---|
| `PhaseManager` | Zustandsmaschine führt durch Setup → Kalibrierung → Zeichnen («phasen-geführt») |
| `Movement` | Kinematik + AccelStepper-Motorsteuerung |
| `Pen` | Servo-Ansteuerung (ESP32Servo) |
| `Display` | SSD1306-OLED: Status, IP-Adresse |
| `Runner` | Liest Befehlsdatei aus dem Flash (LittleFS), orchestriert das Zeichnen |
| Webserver | ESPAsyncWebServer + WiFiManager: Konfiguration ohne Code-Anpassung |

**Web-UI (TypeScript, wird beim Build ins Flash gepackt):** SVG-Upload direkt im Browser; die SVG-Verarbeitung (Skalierung auf die Zeichnungsfläche, Umwandlung in Bewegungsbefehle + Stift hoch/runter) läuft im Browser; das Ergebnis wird als kompakte Befehlsdatei auf den ESP32 hochgeladen und dort Zeile für Zeile ausgeführt. REST-Endpunkte: `/uploadCommands`, `/setTopDistance`, `/run`, `/getState`, `/command`.

**Was das für den Alltag bedeutet:** Die komplette Werkzeugkette aus Plan A (Inkscape → svg2gcode → gcode_wascher.py → SD-Karte) **entfällt**. SVG rein, Zeichnung raus. Auch das «SD-Karten-Shuttle» zwischen Mac und Maschine verschwindet – besonders bequem, wenn die Maschine an der Wand hängt.

**Bauen:** PlatformIO (VS Code) oder Devcontainer; `build.py` packt die Web-UI mit. Keine vorgefertigten Releases/Tags – man kompiliert selbst vom `main`-Branch. Für uns unproblematisch, für Einsteiger die grösste Software-Hürde.

## 7. Projektgesundheit & Community

| Kriterium | Befund | Konfidenz |
|---|---|---|
| Letzter Commit | 05.01.2026 (Devcontainer-Support), 232 Commits total | hoch |
| Versionen | v1.0 (Montagevideo), v1.1 (Update-Video); **keine Git-Releases/Tags** | hoch |
| Community | 298 Stars, 75 Forks, 21 Watcher; Discord-Server; Autor per Kofi-Spende unterstützbar | hoch |
| Presse | Hackaday, Hackster.io, Circuit Digest (je März 2025) | hoch |
| Komplettierung | BOM, STLs, Videos, Kinematik-Dokument – fast alle Bausteine vorhanden | hoch |
| Risiken | Ein-Haupt-Autor-Projekt (Bus-Faktor); kein semantisches Versioning | mittel |

Vergleich Plan B: Polargraph (letztes Release 2017, auf Processing 2.2.1 eingefroren) ist praktisch Geschichte – Mural ist das aktive, moderne Gegenstück in derselben Gattung.

## 8. Lizenz – CC BY-NC 4.0

Code **und** Dokumentation stehen unter [CC BY-NC 4.0](https://github.com/nikivanov/mural/blob/main/LICENSE.md) (© 2025 Nik Ivanov):

- **Erlaubt:** privater Bau, Veränderung, Weitergabe mit Namensnennung.
- **Verboten:** kommerzielle Nutzung (Pläne/Firmware nicht kommerziell einsetzen, keine Plotter nach diesem Design verkaufen).
- Für unser Vorgehen (privates Hobbyprojekt, keine Vermarktung): **unkritisch**.
- Anders als Plan A/B (GPL) also etwas restriktiver im kommerziellen Fall – für uns ohne praktische Bedeutung. Gezeichnete Kunstwerke gehören ohnehin dem Zeichner.

## 9. Stärken / Schwächen / Risiken

**Stärken:**
- Bestes dokumentiertes Kinematik-Modell in der Hobby-Wandplotter-Szene (Konfidenz: mittel-hoch; im Vergleich zu Walldraw/Polargraph/GRBL-Portierungen klar führend)
- Komfort ohne PC-Software: SVG im Browser, keine SD-Karte, keine Gcode-Werkzeugkette
- Zahngurt statt Schnur: dehnungsarm, rutschfest, keine Spulen-Durchmesser-Kalibrierung
- NEMA 17 + TMC2209: stark, schnell, leise, Mikrostepping
- Aktives Projekt, sauberer Code, exzellente Doku, Discord-Community
- Waschbare Stifte = risikofreies Experimentieren an der Wand

**Schwächen / Risiken:**
- **3D-Druck zwingend** – ohne eigenen Drucker entstehen Mehrkosten und Beschaffungslaufzeit
- Keine Releases: selbst kompilieren mit PlatformIO (neues Werkzeug gegenüber Thonny/Arduino IDE)
- Ein-Autor-Projekt mit gemässigem Steam (298 Stars) – weniger Resilienz als Grossprojekte
- Zeichnungsfläche nur 60 % des Pin-Abstands breit; sehr grosse Wandbilder brauchen weite Pin-Abstände
- Genauigkeit laut Autor selbst noch ausbaufähig
- CC BY-NC schliesst kommerzielle Nutzung aus

## 10. Bewertung für Paul – passt Mural zu uns?

| Kriterium | Einschätzung |
|---|---|
| Vorerfahrung | ESP32-Know-how aus MeshCore vorhanden; PlatformIO/VS Code wäre Neuland, aber gut lernbar |
| Werkzeugketten-Komfort | Entfällt fast komplett – nach den Erfahrungen mit svg2gcode/Wascher ein echter Gewinn |
| Beschaffung | Einzelaufträge AliExpress/Amazon (ca. 60 USD) + 3D-Druck-Dienst oder Drucker-Zugang (offene Frage) |
| Zeichnen lernen | Kinematik-Dokument ist auch als Lektüre für die Polargraph-Physik wert – unabhängig vom Bau |
| Zeitaufwand | Etappenbau (Teile beschaffen → drucken → montieren → flashen), gut nebenbei möglich |
| Alternativen | Kit-Verfeinerung (Plan A+) wäre billiger, aber viel weniger präzise |

**Empfehlung:** Plan A (BinHex-Kit) zuerst aufbauen und erleben. Wenn das Zeichen fasziniert und die Kit-Grenzen (Schnurdehnung, Randverzerrung, SD-Shuttle, laute Vollschritt-Motoren) stören, ist Mural der logische, gut dokumentierte Nachfolge-Build. Der Zeitpunkt ist günstig: Projekt aktiv, Doku vollständig (v1.1), Community erreichbar.

## 11. Nächste Schritte, falls Plan D konkret wird

1. 3D-Druck-Zugang klären (eigener Drucker, Dienst, Bekannten-Drucker) – grösste Hürde.
2. BOM über die Amazon-Affiliate-Liste oder AliExpress bestellen (GT2-Riemenscheiben-**Exaktmasse** beachten!).
3. PlatformIO installieren, Firmware einmal unverbindlich kompilieren (ohne Hardware) – Lernstunde ESP32-Toolchain.
4. Nach Plan-A-Erfahrung: Vergleichsmessungen Kit ↔ Mural wären ein schönes BrainGym-Experiment (gleiche SVG auf beiden Maschinen).

## 12. Quellen (Stand 31.10.2026)

- Projekt-Website: https://getmural.me
- GitHub-Repo: https://github.com/nikivanov/mural
- Kinematik-Modell: https://github.com/nikivanov/mural/blob/main/KinematicModel.md
- Stückliste (BOM): https://github.com/nikivanov/mural/blob/main/BOM.md
- Lizenz: https://github.com/nikivanov/mural/blob/main/LICENSE.md
- PlatformIO-Konfiguration: https://github.com/nikivanov/mural/blob/main/platformio.ini
- Montagevideo v1.0: https://www.youtube.com/watch?v=Yg7z5wKEo0o
- Update-Video v1.1: https://www.youtube.com/watch?v=QDJyDLlvLoo
- Hackaday-Besprechung (24.03.2025): https://hackaday.com/2025/03/24/mural-the-plotter-that-draws-on-walls/
- Hackster.io (Nick Bild): https://www.hackster.io/news/a-very-sketchy-robot-9905cfcdda8e
- Circuit Digest (24.03.2025): https://circuitdigest.com/news/diy-open-source-wall-plotter-for-high-precision-drawings-under-100
- DeepWiki-Architektur-Analyse: https://deepwiki.com/nikivanov/mural
