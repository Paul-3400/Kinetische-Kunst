# Plan B – Die Original-Polargraph-Software (Sandy Noble) auf dem BinHex-Kit

**Status:** Recherche abgeschlossen am 29.10.2026. Plan A bleibt der Walldraw-Standard (autonomes Zeichnen von der TF-Karte, «1.nc»). Plan B ist der «Künstler-Modus» mit der Original-Polargraph-Software – PC-gestützte Steuerung mit Vektor- und Pixelzeichnen.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 29.10.2026

Dieses Dokument fasst zusammen, was im Drive-Ordner Polargraph/PCBway liegt, wie alt die Software ist, wo sie heute noch läuft – und was zu tun wäre, um sie auf dem BinHex-Kit einzusetzen.

## 1. Ausgangslage: der PCBWay-Fund

- [PCBWay-Projekt «Drawing Robot Board (Polargraph – Plotter)»](https://www.pcbway.com/project/shareproject/Drawing_Robot_Board_Polargraph_Plotter_fe55b93b.html) von Mert Kiliç: eine eigene Platine, die im Wesentlichen die Elektronik des BinHex-Kits vereint (ATmega328P + CH340G, 2× ULN2003, 2× 28BYJ-48, L7805, Servo-Stiftleiste). Er baut damit einen Tisch-Polargraphen (397 × 546 mm) mit 3D-gedruckten Füssen.
- Der Drive-Ordner enthält das komplette Software-Bündel von [euphy/polargraph](https://github.com/euphy/polargraph) (Sandy Noble, GPL v3): Controller v2.4.2 (Processing-Quellcode + Bibliotheken) und die Arduino-Firmware polargraph_server_a1 samt Bibliotheken und vorcompilierten .hex-Dateien.
- Die mitgelieferte Maschinen-Konfiguration (maker101io-001.properties, Mai 2024) gehört zur Desktop-Maschine des Autors: 397 × 546 mm, 4076 Steps/Umdrehung, 64 mm Schnur pro Umdrehung, Penlift 90°/40°, 57600 Baud.

## 2. Architektur der Polargraph-Software

| Komponente | Läuft auf | Aufgabe |
|---|---|---|
| Polargraph Controller v2.4.2 | PC (Processing 2.2.1) | Bedienoberfläche: Bild laden, in Fahrbefehle umwandeln, Warteschlange an die Maschine senden – Vektor- UND Pixelzeichnen (Halftone/Dichte-Schraffur), Vorschau, manuelle Fahrten |
| polargraph_server_a1 | Arduino UNO | Firmware: nimmt ASCII-Befehle über USB-Seriell (57600 Baud) entgegen, fährt die Schrittmotoren über AccelStepper |

**Schlüsselbefund:** Die Firmware enthält einen Modus `UNL2003_DRIVER` (Community-Beitrag von @j0nson) für 28BYJ-48-Motoren an ULN2003-Treibern – exakt die Hardware-Klasse des BinHex-Kits. Die Pin-Belegung im Code (MotorA 6/7/8/9, MotorB 2/3/4/5) weicht von der Walldraw-Verkabelung ab (links 7/8/9/10, rechts 2/3/5/6) und wäre in den AccelStepper-Pin-Arrays anzupassen – eine überschaubare Codeänderung.

## 3. Alters-Check: wird die Software noch gepflegt?

### Processing (die Laufzeitumgebung des Controllers)

| Version | Datum | Status |
|---|---|---|
| 2.2.1 | September 2014 | **Letzte 2.x-Version.** Wird nicht mehr gepflegt – auf processing.org nur noch als «Legacy/Archiv, ohne Support» geführt. Der Controller läuft NUR auf 2.2.1 |
| 3.5.4 | Januar 2020 | letzte 3.x-Version; der alte Controller läuft laut Autor ausdrücklich NICHT unter Processing 3 |
| 4.5.7 | 24.09.2026 | **aktuell**, aktiv gepflegt (Java 17, Apple-Silicon-nativ) – für den alten Controller jedoch unbrauchbar |

### Polargraph-Software selbst

| Objekt | Stand (29.10.2026) |
|---|---|
| Controller v2.4.2 | **letztes offizielles Release**, 10.05.2017 – identisch mit dem Bündel im Drive-Ordner |
| Nachfolge-Release 01.11.2017 | nur Neupaketierung ohne macOS-Binary (das alte macOS-Binary löste eine Virenwarnung aus) |
| GitHub-Repo euphy/polargraphcontroller | letzte Commits um 2020, seither keine Aktivität; kein Port auf Processing 3/4 |
| polargraph.co.uk-Forum | letzter Beitrag Juli 2018 – das Projekt schläft |
| Community-Forks | existieren (z. B. Refactoring-Fork drvnprgrmr), bleiben aber alle bei Processing 2.2.1 |

**Fazit Alters-Check:** Processing 2.2.1 wird seit 2014 nicht mehr unterhalten, die Polargraph-Software seit 2018/2020 nicht mehr weiterentwickelt. Sie ist «Fossil, aber funktional» – die Befehlssprache Controller↔Firmware ist stabil und in sich abgeschlossen. (Konfidenz hoch)

## 4. Lauf-Umgebungs-Check: wo läuft der Controller heute?

### 4.1 MacBook Air M2 (Apple Silicon) – Konfidenz mittel

Processing 2.2.1 gibt es nur als Intel-Build (x86_64) – auf dem M2 läuft er ausschliesslich über **Rosetta 2**. Das ist kein Hinderungsgrund, aber ungetestet: altes Java/AWT auf aktuellem macOS kann Rendering- oder Stabilitätsprobleme machen. Der Testaufwand beträgt ca. 30 Minuten:

1. Rosetta installieren (falls noch nicht geschehen): `softwareupdate --install-rosetta`
2. Processing 2.2.1 (macOS) von processing.org laden und entpacken; Quarantäne entfernen: `xattr -dr com.apple.quarantine <Ordner>`
3. Aus dem Drive-Bündel die Processing-Bibliotheken (geomerative, ControlP5, Diewald) in den Ordner «libraries» des Processing-Sketchbooks kopieren, den Controller-Ordner in den Sketchbook-Ordner
4. Processing starten, Sketch polargraphcontroller öffnen, Run drücken

### 4.2 Raspberry Pi 4B – Konfidenz mittel, mit handwerklicher Vorarbeit

Es gibt **keinen fertigen ARM-Build von Processing 2.2.1** – der Linux-Download enthält ein x86-Java. Bewährtes Rezept (Adhira Tech, 2021, demonstriert am Pi 2):

1. Processing 2.2.1 «linux32» herunterladen und entpacken
2. Das mitgelieferte Java löschen und durch ein ARM-JDK 8 ersetzen (Symlink auf den Java-Ordner)
3. Die serielle Bibliothek jSSC gegen eine Version mit ARM-Native-Code tauschen (jSSC 2.6/2.9)

Zwei praktische Hürden bei uns:

- Unsere Pi-4Bs laufen mit **Pi OS 13 (64-bit/aarch64)**. Der Java-Swap braucht dann ein aarch64-JDK 8 und ein jSSC mit ARM64-Natives – plausibel, aber ungetestet (Konfidenz niedrig). Sauberer wäre eine **eigene SD-Karte mit 32-bit-Pi-OS** nur für den Zeichnerbetrieb (Konfidenz mittel, bewährtes Rezept).
- Der Controller braucht eine **grafische Oberfläche** (Desktop oder VNC-Session) – headless geht nicht.

**Aber: beide Pi 4B sind in Dauereinsatz** (RpPi4B-001 CoreScope/MeshCore-Observer, RpPi4B-002 BirdNET-Go; Stand Hardware-Inventar 20.09.2026). Optionen:

| Option | Bewertung |
|---|---|
| Zusätzliche GUI-Session auf RpPi4B-002 neben BirdNET (4 GB RAM) | möglich, da der Controller nur während des Zeichnens läuft – aber Belastung des produktiven Vogel-Erkenners; vorher RAM-Check |
| Eigene 32-Bit-SD-Karte, Dienste temporär pausieren | funktioniert, unterbricht aber CoreScope/BirdNET – für produktive Dienste nicht empfohlen |
| Dedizierter (gebrauchter) Pi 4B als «Zeichen-Computer» | sauberste Lösung, ca. CHF 50–70 – nur nötig, wenn Plan B zum Lieblingsweg wird |
| Pi Zero W / Zero 2 W | ungeeignet (armv6/zu wenig RAM) bzw. belegt (INA226-Steuerung) |

### 4.3 Was sicher NICHT geht

- Der alte Controller unter Processing 3 oder 4 (aktuell 4.5.7) – explizit nicht kompatibel
- Betrieb ohne GUI / ohne verbundenen PC (das ist der Unterschied zu Plan A: Walldraw zeichnet autonom von der TF-Karte)

## 5. Empfehlung: Entscheidungsbaum

1. **Plan A zuerst:** nach Lieferung des Kits die Walldraw-Kette in Betrieb nehmen (WallDrawDemo.ino → Maschinenwerte → Schneemann/1.nc). Sie ist unabhängig von allem Alt-Software-Risiko.
2. **Plan B ausprobieren, wenn das Kit läuft:** zuerst der 30-Minuten-Test auf dem MacBook Air (Rosetta, Kap. 4.1). Kostet nichts ausser Zeit.
3. **Falls der Mac scheitert:** Raspi-Variante nach Kap. 4.2 – vorerst nur testen, keine Anschaffung, solange unklar ist, ob Plan B gefällt.
4. **Falls beides scheitert:** Plan C (Kap. 6) – oder man geniesst Plan A weiter, denn Zeichnungen wie der Schneemann funktionieren ohnehin autonom.

## 6. Plan C – Ausblick auf aktive moderne Projekte (Stand 2026)

Für den Einstieg mit dem BinHex-Kit nicht relevant, aber gut zu wissen, wohin die Szene gewandert ist (alle mit anderer Hardware als dem Kit):

- [Mozieyo/polargraph](https://github.com/Mozieyo/polargraph) – Browser-Studio (generative Bild-Engines), PC-Pipeline SVG → Gürtellängen-G-code, gestreamt auf einen RP2040 mit grblHAL; aktiv 2026
- [arvandtiv/polar-plotter](https://github.com/arvandtiv/polar-plotter) – Raspberry Pi Pico 2 W + TMC5072-Dual-Steppertreiber, Web-Konsole mit Kalibrier-Matrix; aktiv 2026
- [ramon-umleal/grbl-polargraph](https://github.com/ramon-umleal/grbl-polargraph) – GRBL-Fork für Wandzeichner (NEMA17, GT2-Riemen)
- [CreativeTab/MarlinPolargraph](https://github.com/CreativeTab/MarlinPolargraph) – Marlin-Adaption für hängende V-Plotter

## 7. Anpassungs-Checkliste für den Ernstfall (Plan B auf dem BinHex-Kit)

| Schritt | Details |
|---|---|
| 1. Firmware anpassen | polargraph_server_a1 mit `UNL2003_DRIVER` kompilieren; AccelStepper-Pin-Arrays auf die Walldraw-Verkabelung umschreiben (links 7/8/9/10, rechts 2/3/5/6) |
| 2. Arduino flashen | Arduino IDE (der Autor empfiehlt 1.8.5 für alte Bibliotheken; aktuellere IDEs ausprobieren, bei Fehler zurückfallen) |
| 3. Controller einrichten | Processing 2.2.1 + Bibliotheken; Maschinenwerte im Setup-Tab: Breite/Höhe ausmessen, mmPerRev ≈ 110 (Spulendurchmesser 35 mm × π), Steps per Rev 2048 (Vollschritt) bzw. 4076/4096 (Halbschritt) je nach Treibermodus, Step multiplier entsprechend, Home-Punkt definieren |
| 4. Verbindung | USB-Seriell 57600 Baud; ggf. CH340-Treiber auf dem Mac (UNO-Nachbau im Kit) |
| 5. Erste Fahrt | Testseite fahren: Quadrat, Referenzlinien, dann kleine Vektorzeichnung; erst danach Pixelzeichnen |

Lizenzbremse: alles GPL v3 – nutzen und anpassen ist frei; eigene Änderungen an der Firmware müssen bei Weitergabe offen liegen.

## 8. Quellen (Stand 29.10.2026)

- Processing-Releases (Legacy-Archiv 2.x, aktuell 4.5.7): https://processing.org/releases
- Polargraph-Controller-Repo (README: «Running on Processing v2.2.1»): https://github.com/euphy/polargraphcontroller
- Controller-Releases (v2.4.2, 10.05.2017; Repackaging 01.11.2017): https://github.com/euphy/polargraphcontroller/releases
- Original-Bündel (identisch mit Drive-Ordner): https://github.com/euphy/polargraph
- Processing 2.2.1 auf Raspberry Pi (Java-Swap-Rezept): https://adhiratech.com/2021/12/15/raspberry-pi-2-can-run-processing-2-2-1/
- Processing for Pi (deprecated, 3.5.3 armv6hf): https://pi.processing.org/download/
- Processing 4 ARM-Builds (32/64-bit): https://github.com/processing/processing4/releases
- PCBWay-Projekt Drawing Robot Board: https://www.pcbway.com/project/shareproject/Drawing_Robot_Board_Polargraph_Plotter_fe55b93b.html
