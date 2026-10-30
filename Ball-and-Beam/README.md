# Ball & Beam – PID-Regelung mit PTFE-Vollkugel

**Kinetisches Objekt und Regelungstechnik-Experiment in einem:** Eine PTFE-Vollkugel (35 mm, bestellt 24.10.2026) rollt auf einer Schiene (Kompaktvariante ~350 mm; Antriebsvariante «lang» ~650 mm, siehe eigener Abschnitt). Ein Antrieb kippt die Schiene, ein Laser-ToF-Sensor misst die Ballposition, und ein PID-Regler hält den Ball aktiv auf der Sollposition. Ohne Regelung rollt der Ball unweigerlich davon – die Strecke ist ein instabiler Doppel-Integrator und damit ein Klassiker der Regelungstechnik.

## Funktionsweise

- **Physik (kleine Winkel):** r'' = K · sin(θ) mit K ≈ 0.6 · g für Hohlkugeln (Ping-Pong) bzw. K = 5/7 · g ≈ 0.71 · g für Vollkugeln (PTFE, Golfball). Der Drehpunkt (Mitte oder Ende) geht nicht in die Bewegungsgleichung ein – nur der Balkenwinkel zählt. K ist am echten Aufbau einzumessen (Kalibrierfahrt mit bekanntem Winkel).
- **Sensor:** VL53L1X (Laser-ToF, I²C) fest am einen Schienenende; misst die Ballposition entlang der Schiene mit bis zu 50 Hz, ohne tote Zone, ROI einengbar. Ultraschall (HC-SR04) wurde bewusst verworfen: kleines kugelförmiges Ziel mit schwachem Echo, träger ~60-ms-Messzyklus. Alternative: Sharp GP2Y0A41SK0F (4–30 cm, analog, nichtlinear) oder Kamera + OpenCV bei bewegtem Ball.
- **Antrieb:** Kompaktvariante: Servo MG90S, maximal ±7°. Variante «lang»: Stepper mit Scheibenrad und Pendelsteigbügel (siehe unten).
- **Regler:** Diskreter PID-Regler mit 50 Hz Abtastzeit:
  - D-Anteil auf der Messung statt auf dem Fehler (kein «D-Kick» bei Sollwertsprüngen)
  - Tiefpass auf dem D-Anteil gegen Sensorrauschen
  - Anti-Windup (I-Anteil begrenzt) und Ausgangsbegrenzung (Balkenwinkel)

## Konstruktionsentscheide – Drehpunkt am Schienenende (Konfiguration B)

**Entscheid (24.10.2026):** Der Drehpunkt liegt am einen Schienenende, der Antrieb greift am anderen Ende an («Wipp-/Kranprinzip»). Die Ball-Physik ändert sich dadurch nicht (weiterhin r'' = K · sin(θ)), wohl aber die Aktor-Geometrie:

| Eigenschaft | A: Drehpunkt Mitte, Antrieb am Ende | B: Drehpunkt Ende, Antrieb am Ende (gewählt) |
|---|---|---|
| Hebelarm des Angriffs | ~175 mm | Schienenlänge |
| Hubbedarf am Angriffspunkt für ±7° | ±21 mm (bei 350 mm) | ±73 mm (bei 600 mm) |
| Winkel-Auflösung (0,1 mm Hub) | 0,57 mrad | 0,29 mrad (feiner) |
| Spiel am Angriff (0,5 mm) → Winkelfehler | 1,6 mrad | 0,8 mrad (halber Fehler) |
| Kraft am Angriff | ~Balgewicht | geringer (doppelter Hebel) |

**Eingegangene Konsequenzen und Massnahmen:**

1. **Winkelvorrat sicherstellen:** Kompaktvariante: Standard-Servoarm (20 mm, ±60° ≈ ±17 mm Hub) erreicht nur ±2,8° – geplant: Servoarm ~40 mm oder Kurbel-Schubstange für ±5–7°. Variante «lang»: Bohrradius R am Scheibenrad (siehe dort).
2. **Gegengewicht hinter dem Drehpunkt:** Nur bei direkt kippendem Antrieb relevant (Dauerdrehmoment des Schienengewichts, Holding-Jitter); bei der Steigbügel-Variante trägt der Bügel den Balken dauerhaft – entfällt.
3. **Sensor auf der Schiene montieren:** Der VL53L1X sitzt auf der Schiene am Drehpunkt-Ende und dreht mit – er misst dann die wahre Ballposition r. Starr am Rahmen montiert, sähe er nur die Projektion r · cos(θ) (bei ±7° bis ~2,6 mm winkelabhängiger Fehler). Am Drehpunkt bewegt er sich im Raum kaum, dreht aber korrekt mit.

**Reglerwerte für die Kompaktvariante mit kurzem Servoarm** (Simulation, ±2,8°, Servo ~1 rad/s Balkenwinkelgeschwindigkeit): **Kp = 10, Ki = 1, Kd = 4** → Überschwingen ~8 mm, eingeschwungen in ~3,2 s. Die Werte für ±7° (Kp = 4, Ki = 0.5, Kd = 1.2) sind mit der Kurzarm-Geometrie zu weich (~28 mm Überschwingen).

**In der Simulation nachspielbar:** im Skript `THETA_MAX = math.radians(2.8)` und `SERVO_RATE = 1.0` setzen und die Reglerwerte oben eintragen.

## Ball-Entscheid – PTFE-Vollkugel statt Ping-Pong-Ball (24.10.2026)

**Entscheid:** Als Regelobjekt wird eine **PTFE-Vollkugel mit 35 mm Durchmesser** eingesetzt (bestellt 24.10.2026; liegt im empfohlenen Fenster 30–40 mm; ~49 g, ROI-4×4-Fleckdeckung ~14 % bei 350 mm).

**Begründung:**

1. **Optisch ideal für den ToF-Sensor:** Gesintertes PTFE ist das Referenzmaterial der Optik – die Labsphere-«Spectralon»-Standards basieren darauf (>99 % Remission im Bereich 400–1500 nm, also auch beim 940-nm-Laser des VL53L1X) mit nahezu perfektem Lambert-Verhalten, d. h. ideal diffuse Streuung ohne Spiegelartefakte. Bester möglicher Photon-Rückfluss, robust gegen Fremdlicht.
2. **Vollkugel statt Hohlkugel:** Ein Ping-Pong-Ball ist so leicht (2,7 g), dass er auf Schienen tendenziell rutscht statt rollt – das reale K weicht vom Modell ab, die Regelung leidet. Die schwere PTFE-Kugel rollt sauber; das Modell r'' = K · sin(θ) stimmt besser.
3. **Gewicht macht Reibung vernachlässigbar:** PTFE ~2,2 g/cm³ (30 mm ≈ 31 g, 35 mm ≈ 49 g, 40 mm ≈ 74 g). Trotz niedriger PTFE-Reibung (µ ≈ 0.1) reicht die Rollhaftung bei ±7° Balkenwinkel locker aus (benötigt wären µ ≈ 0.04).
4. **Preislich und beschaffungsmässig unproblematisch:** PTFE-Kugeln sind in gängigen Durchmessern erhältlich.

**Konsequenz für die Strecke:** K steigt von 0.6 · g (Hohlkugel) auf 5/7 · g ≈ 0.71 · g (+18 % Streckenverstärkung). K wird ohnehin per Kalibrierfahrt eingemessen; die Reglerstruktur bleibt unverändert (Retuning nach Erstbetrieb).

**Mindest-Durchmesser-Kriterien (massgebend für das Wahl-Fenster 30–40 mm):**

| Kriterium | Untergrenze | Begründung |
|---|---|---|
| Sensor-Signal | ≥ 25 mm, komfortabel 30–40 mm | Fleckdeckung: bei 350 mm mit ROI 4×4 (Fleck ~92 mm) ≈ 14 %; bei 600 mm (Fleck ~158 mm) nur noch ~4,9 % → Timing-Budget erhöhen (siehe Variante «lang») |
| Schienenführung | Durchmesser ≥ 1.2–1.5 × Schienenmittenabstand | Sonst sitzt die Kugel zu flach im «Tal» und läuft seitlich weg. Bei 35 mm Kugel → Schienenabstand ~23–29 mm, gewählt ~25 mm |
| Rolldynamik | ≥ 25 mm | Unempfindlichkeit gegen Schienen-Fugen und Rundheitstoleranzen; genügend Masse gegen Reibungseinflüsse |
| Sensor-Totzone | Ballfront nie näher als ~40 mm an den Sensor | Mindestmessdistanz des VL53L1X (4 cm) → mechanischer Anschlag entsprechend setzen |

**Sensoreinstellungen dazu:** ROI auf 4×4 oder 8×8 einengen und auf die Schienenachse zentrieren; Timing-Budget ~50 ms (Kompaktvariante) bzw. 50–100 ms (Variante «lang»).

## Antriebsvariante «lang» (30.10.2026): Stepper mit Scheibenrad und Pendelsteigbügel

**Konzept:** Balken ~650 mm, einseitig am Drehpunkt gelagert. Statt Servo von unten: Steppermotor mit angeflanschtem Scheibenrad (Pulley). Ein pendelnd gelagerter, steigbügelartiger Bügel hängt am Kurbelbolzen und greift den Balken, der nur im Bügel liegt. Der Bolzen ist auf verschiedenen Radien des Scheibenrads montierbar; der Bügel ist längenverstellbar.

**Kinematik:** Das ist ein Kurbeltrieb mit Pendelentkopplung (Scotch-Crank-Prinzip). Der Pendelbügel überträgt nur Vertikalkraft (Balken kann im Sattel kippen und gleiten); die Höhenbewegung des Balkens am Angriffspunkt folgt dem Bolzen: **sin(θ) = (R / L_z) · sin(α)** mit R = Bohrradius, L_z = Abstand Angriffspunkt ↔ Drehpunkt, α = Scheibenwinkel. Neutralstellung: α = 0 (Bolzen auf Halbhöhe), Bügellänge so wählen, dass der Balken waagrecht steht.

**Die zentrale Konstruktionsgleichung:**

sin(θ_max) = R / L_z → **R = L_z · sin(θ_max)**

| Bohrradius R bei L_z = 600 mm | max. Balkenwinkel |
|---|---|
| 30 mm | ±2,9° |
| 40 mm | ±3,8° |
| 50 mm | ±4,8° |
| 60 mm | ±5,7° |
| 73 mm | ±7,0° |

Für ±7° braucht es also z. B. R = 37 mm bei L_z = 300 mm, R = 55 mm bei 450 mm, R = 73 mm bei 600 mm. **Konstruktionsregel: Bohrkreis bis ~75 mm vorsehen** (oder Angriffspunkt Richtung Drehpunkt). Wichtig: Bei festem Winkelvorrat ±7° ist die Übersetzung dθ/dα = R/L_z = sin(7°) ≈ 0,12 immer gleich – ein kleineres R macht nichts feiner, es schmälert nur den Winkelvorrat.

**Warum diese Variante mechanisch elegant ist:**

- **Pendelgelenk am Kurbelbolzen:** nur Vertikalkraft auf den Balken, keine Horizontalkräfte ins Scheibenlager; der Balken kann im Sattel frei kippen.
- **Schwerkraft-vorgespannter Kraftweg:** der Balken liegt im Bügel, die Schwerkraft sitzt ihn fest → praktisch spielfreie vertikale Übertragung (kein Gegenspiel wie beim Servoarm).
- **Stepper statt Servo:** keine Totzone, Mikrostepping (z. B. 3200 Mikroschritte/Umdrehung → 1,96 mrad) → **0,13–0,24 mrad Balkenwinkel pro Mikroschritt** – weit feiner als jeder Hobby-Servo.
- **Drei Stellschrauben:** Bohrradius R (Winkelvorrat), Angriffsposition L_z (Übersetzungskompromiss Kraft ↔ Radiengrösse), Bügellänge (Neutralhöhe).
- **Sinusübertragung:** der cos(α)-Faktor senkt die effektive Übersetzung an den Endlagen automatisch ab – die Regelung wird an den Rändern sanfter, nicht härter.
- **Kehrseite der Sinusübertragung (Update 30.10.2026):** derselbe Faktor lähmt die Balken-Umkehr am Vollausschlag (dθ/dα → 0 bei α = ±90°): Eine Umkehr von −7° auf +7° erfordert einen 180°-Kurbelschwung. Deshalb **Kurbelrate ≥ 720°/s** und softwareseitigen **Reglerbereich ±5°** einplanen (siehe «Kurbelrate und Umkehrverhalten»).

**Auslegungszahlen (L_z = 600 mm, R = 73 mm, ±7°):** Kurbelwinkel ±90° (Viertelkreis je Seite); Bolzenhub ±73 mm; Kraft am Bügel ~1–2 N (Balken ~0,3–0,5 N·m) – ein NEMA17 mit TMC2209-Treiber ist überdimensioniert genug; Balkenschwenkgeschwindigkeit ~1,2 rad/s erfordert ~10 rad/s Kurbeldrehzahl (≈ 95 U/min) – Standardgebiet.

**Simulations-Ergebnisse** (K = 5/7·g, Ballbereich 50–600 mm, Soll 300 mm, Sensorrauschen ±4 mm, Median-Filter, exakte Kurbelkinematik):

Die erste Abschätzung (24.10.2026) mit der Näherung slew ≈ Kurbelrate · R/L_z und Kp=4/Ki=0.5/Kd=1.2 kam auf ~21 mm/~2,2 s. Die exakte Kurbelsimulation (30.10.2026, Skript `ball_and_beam_lang.py`) korrigiert das: **Entscheidend ist die Kurbelrate** (Abschnitt unten). Korrigierte Werte:

| Konfiguration | Kurbelrate | Regler (Bereich ±5°) | Überschwingen | Eingeschwungen |
|---|---|---|---|---|
| R = 73 mm (±7°), Start 550 mm | 720°/s (2 U/s) | Kp=3, Ki=0.5, Kd=1.5 | ~10–12 mm | ~1,2–1,7 s ✅ |
| R = 73 mm, Start 120 mm (Gegenrichtung) | 720°/s | Kp=3, Ki=0.5, Kd=1.5 | ~9 mm | ~1,5 s ✅ |
| R = 73 mm, Start 550 mm | 360°/s | Kp=3, Ki=0.5, Kd=1.5 | ~160 mm | ⚠️ Grenzzyklus |
| R = 40 mm (±3,8°), Start 550 mm | 720°/s | Kp=3, Ki=0.5, Kd=1.5 | ~45–70 mm | träge ⚠️ |

Interpretation: **Zwei Konstruktionsparameter sind kritisch:** (1) Der Bohrradius R begrenzt die Stellautorität – R = 40 mm bleibt auch mit gutem Regler träge. (2) Die Kurbelrate begrenzt die Umkehr-Agilität – bei 360°/s gerät der Regelkreis in einen Grenzzyklus zwischen den Anschlägen.

### Kurbelrate und Umkehrverhalten (Update 30.10.2026)

Die Umkehrung der Kinematik lautet dθ/dα = (R/L_z) · cos(α) / cos(θ). Am Vollausschlag (α = ±90°) kollabiert sie: Der Balken bewegt sich kaum, während die Kurbel eilig läuft. Eine Balken-Umkehr von −θ_max nach +θ_max erfordert einen **Kurbelschwung von 180°** – Zeitbedarf t = π / Kurbelrate:

| Kurbelrate | Umkehrzeit (±7°-Bereich) | Simulation |
|---|---|---|
| 180°/s (1 U/s) | 1,0 s | instabil |
| 360°/s (2 U/s) | 0,5 s | Grenzzyklus |
| 720°/s (2 U/s = 120 U/min) | 0,25 s | stabil ✅ |

Zweite Stellschraube: den **Reglerbereich softwareseitig auf ±5° begrenzen** (die Konstruktion behält ±7° als Reserve). Dann erreicht die Kurbel nur α ≈ ±46°, und der nötige Umkehrschwung schrumpft von 180° auf ~92° → 0,13 s bei 720°/s. Die Reserve zahlt sich doppelt aus: mehr Toleranz gegen Fundament-Neigung und schnellere Umkehr.

**Empfehlung: Kurbelrate ≥ 720°/s einplanen** – für einen NEMA17 mit TMC2209 trivial (~120 U/min); zugleich Reglerbereich softwareseitig auf ±5° begrenzen.

**Zu beachten (Entscheide/Offenpunkte):**

1. **Sensorabdeckung am fernen Ende:** Bei 600 mm Distanz deckt die 35-mm-Kugel im ROI 4×4 (Fleck ~158 mm) nur noch ~4,9 % ab – an der Grenze der Faustregel. Gegenmittel: Timing-Budget auf 50–100 ms erhöhen (Messrate 10–25 Hz – dem langsamen Langbalken reicht das), Median- oder EMA-Filter über 2–3 Werte. Die Reichweite des VL53L1X (bis 400 cm) ist nie das Problem.
2. **Der Balken liegt nur im Bügel:** Der Mechanismus kann nur heben, nicht drücken. Im Normalfall sitzt die Schwerkraft den Balken fest; bei Fundament-Beschleunigungen (Anfahren/Bremsen/Vibration) kann der Balken aber aus dem Sattel gehoben oder seitlich verschoben werden → **Niederhalter/Seitensicherung am Bügel** vorsehen und Längsspiel begrenzen (bei 7° wandert der Auflagepunkt horizontal um ~4,4 mm – einkalkulieren).
3. **Nullpunkt/Homing:** Der Stepper ist ein offener Winkelzähler → nach dem Einschalten Referenzfahrt nötig: Referenzschalter bei α = 0 (Balken waagrecht) oder MPU6050-IMU am Balken (ohnehin wegen Fundament-Neigung geplant).
4. **650-mm-Balken einseitig gelagert:** steifes Profil wählen (Eigendurchbiegung); Abstützung an Drehpunkt und Bügel ist statisch bestimmt. Gegengewicht hinter dem Drehpunkt entfällt – der Bügel trägt dauerhaft.
5. **Resonanzen:** TMC2209 (leise, mit Rampen) verwenden; Mittfrequenzresonanz des Steppers und Pendeln des Bügels (L ≈ 0,2 m → Periode ~0,9 s) beachten, Bügel seitlich stabil führen oder dämpfen.

## Fundament-Einflüsse: Neigen und Fahren (24.10.2026)

**Physik:** Für den Ball zählt nur der *absolute* Balkenwinkel zur Horizontalen. Mit Fundament-Neigung φ und Fundament-Beschleunigung a (in Auslegerrichtung) gilt:

r'' = K · (sin(θ + φ) − (a/g) · cos(θ + φ))

Alle Fundament-Störungen sind damit dieselbe Währung – **additiver Winkel am Streckeneingang**:

| Störung | Äquivalent am Streckeneingang |
|---|---|
| Fahren mit Beschleunigung a | Δθ = a/g (1 m/s² ≡ 5,8°) |
| Statische Fundament-Neigung φ | Δθ = φ (1:1) |
| Wippen/Vibration (Amplitude A, Frequenz f) | Δθ = A·sin(ωt), bei höheren Frequenzen kaum wirksam |

**Neigen (statisch):** Der PID absorbiert die Neigung, indem der Antrieb dauerhaft einen Gegenwinkel hält – geliefert vom I-Anteil, der durch Anti-Windup auf Ki · I_MAX ≈ 2,9° begrenzt ist. Simulations-Ergebnisse (±2,8°-Vorrat): 1° → unkritisch (~7 mm Einschwingen); 2° → Grenzbereich; **3° → Versagen**: Balken am Anschlag, der Ball läuft bis zum Schienenende. Toleranz ≈ Winkelbudget minus Regel-Reserve:

| Winkelvorrat | Max. statische Fundament-Neigung |
|---|---|
| ±2,8° (Standard-Servoarm) | ~2° |
| ±5,5° (40-mm-Arm) | ~4–4,5° |
| ±7° (Kurbel/Steigbügel) | ~5,5–6° |

**Wippen (dynamisch):** Harmloser als statisch – 0,5° Amplitude (0,5 oder 2 Hz) gibt nur ~5–6 mm Abweichung; der Ball ist als träge Masse für schnelles Wippen unempfindlich. Statisch ist gefährlicher als dynamisch.

**Fahren:** Gleichförmige Fahrt stört nicht (Galilei-Invarianz), nur Anfahren/Bremsen (Δθ = a/g). Grenze: a_max = g · tan(θ_max) → 0,48 m/s² bei ±2,8°, ~1,2 m/s² bei ±7°. Massnahmen: Rampen statt Sprünge sowie **Störgrossen-Aufschaltung** θ_ff = arctan(a/g) (Simulation: 13 → 5 mm Auslenkung bei 0,3 m/s²). Damit ist die Skulptur grundsätzlich «fahrfähig» – Fundament als zweite Stellgrösse in einer Kaskade. Achtung bei der Steigbügel-Variante: Anfahren/Bremsen kann den Balken aus dem Bügelsattel heben → Niederhalter (siehe Variante «lang»).

**Seitliche Neigung:** Anderer Modus, viel toleranter: Mit dem Schienen-Sattel (35-mm-Kugel, 25-mm-Mittenabstand) rollt die Kugel erst ab ~45° aus. Nur die Kippachse ist der empfindliche Modus.

**Drei Massnahmen gegen Fundament-Neigung (nach Aufwand):**

1. **Fundament mit Libelle waagrecht ausrichten** (einmalig beim Aufbau).
2. **I_MAX anheben**, wenn die Umgebung neigt (z. B. 0.05 → 0.12 rad·s erlaubt ~7° Bias) – sonst schlägt die Anti-Windup-Bremse knapp vor dem Antriebs-Limit zu.
3. **IMU (MPU6050, ~CHF 5) am Balken:** absoluten Winkel (θ+φ) messen und als innere Kaskade den *absoluten* Winkel regeln → das System wird neigungs-invariant. Die sauberste Lösung für kinetische Kunst.

## Simulation (ball_and_beam_pid.py)

Reine Python-Simulation ohne Zusatzpakete (läuft direkt in Thonny; matplotlib optional). Ausgabe: ASCII-Verlauf der Ballposition und Kennzahlen (Überschwingen, maximale Abweichung, Einschwingzeit ±5 mm, Restfehler). Enthält ein auskommentiertes Hardware-Skelett für den Echtbetrieb am Raspberry Pi (VL53L1X, gpiozero + PiGPIOFactory, pigpiod; optional MPU6050-IMU für absolute Winkelregelung).

Seit 24.10.2026 rechnet das Skript voreingestellt mit **K = 5/7 · g** (PTFE-Vollkugel); für eine Hohlkugel (Ping-Pong) `K_STRECKE = 0.6 * G` setzen. Für die Variante «lang»: `R_MIN, R_MAX = 0.05, 0.62` setzen.

**Fundament-Modus im Skript** (Umgebung simulieren, ohne den Regler zu ändern):

| Parameter | Wirkung |
|---|---|
| `FUNDAMENT_NEIGUNG_GRAD` | statische Fundament-Neigung in der Kippachse |
| `FUNDAMENT_WIPPEN_AMPL_GRAD` / `FUNDAMENT_WIPPEN_HZ` | sinusförmiges Wippen |
| `FAHREN_A`, `FAHREN_ANFAHREN_S`, `FAHREN_KONSTANT_S` | Trapez-Fahrprofil (anfahren → konstant → bremsen) |
| `FEEDFORWARD` | Störgrossen-Aufschaltung θ_ff = arctan(a/g) ein/aus |

Getestete Regler-Startwerte für ±7° Winkelvorrat (bei ±2 mm simuliertem Sensorrauschen):

| Parameter | Wert |
|---|---|
| Kp | 4.0 |
| Ki | 0.5 |
| Kd | 1.2 |
| Abtastzeit | 20 ms (50 Hz) |
| max. Balkenwinkel | ±7° |

Ergebnis (PTFE-Kugel, Kompaktvariante): Überschwingen ca. 5 mm, eingeschwungen in unter 2 s; robust bis ±5 mm Sensorrauschen.

**Zweites Skript `ball_and_beam_lang.py` (30.10.2026):** Simulation der Variante «lang» mit exakter Kurbelkinematik – sin-Gesetz statt linearer Näherung, Mikroschritt-Quantisierung (3200 µSteps/U), Kurbelraten-Limit, Median-Filter über 3 Messungen, ±4 mm Rauschen, Ballbereich 50–600 mm – inklusive Fundament-Modi und Hardware-Skelett (NEMA17 + TMC2209 STEP/DIR, Homing-Schalter bei α = 0). Getestete Startwerte: **Kp=3, Ki=0.5, Kd=1.5, D-Filter 0.2, Kurbelrate 720°/s, Reglerbereich ±5°** → ~10 mm Überschwingen, ~1,5 s Einschwingen (robust über Startpositionen 120–550 mm).

## Tuning-Rezept für den echten Aufbau

1. Ki = 0, Kd = 0: Kp erhöhen, bis der Ball kräftig zum Sollwert läuft, aber als Pendel schwingt.
2. Kd erhöhen, bis das Pendeln gedämpft ist (Hauptabgleich).
3. Ki vorsichtig erhöhen, bis der Reibungs-Restfehler verschwindet (10–20 % von Kp als Faustregel).
4. Bei Zittern: zuerst D-Filter stärker einstellen, dann Kd senken.

## Geplante Hardware

**Kompaktvariante (~350 mm):**

- 2× Alu-U-Profil oder Vorhangschienen-Paar als Schiene, Mittenabstand ~25 mm
- **PTFE-Vollkugel 35 mm** (Ball-Entscheid, siehe oben)
- Drehpunkt am einen Schienenende, Heber (MG90S) am anderen Ende (Konfiguration B, siehe oben)
- Verlängerter Servoarm (~40 mm) oder Kurbel-Schubstange

**Variante «lang» (~650 mm):**

- Steifes Schienenprofil ~650 mm, einseitiger Drehpunkt, Mittenabstand ~25 mm
- **PTFE-Vollkugel 35 mm** (wie gehabt)
- NEMA17-Stepper + TMC2209-Treiber + angeflanschtes Scheibenrad mit **Bohrkreis R = 30–75 mm**; **Kurbelrate ≥ 720°/s** und softwareseitiger Reglerbereich ±5°
- Pendelnder Steigbügel (Länge verstellbar für Neutralhöhe), Angriff am Balken bei L_z (Empfehlung: fernes Ende, L_z ≈ 600 mm → R = 73 mm für ±7°; Alternativ-Kompromiss L_z ≈ 450 mm → R = 55 mm)
- **Niederhalter/Seitensicherung** am Steigbügelsattel (Balken liegt nur)
- Referenzschalter bei α = 0 oder MPU6050-IMU am Balken (Homing + absolute Winkelregelung)
- VL53L1X auf der Schiene am Drehpunkt-Ende; ROI 4×4/8×8, **Timing-Budget 50–100 ms** wegen Abdeckung bei 600 mm
- Raspberry Pi mit I²C, gpiozero + pigpiod

## Quellen

- Control Tutorials for MATLAB and Simulink – Ball & Beam: System Modeling und PID Controller Design (ctms.engin.umich.edu)
- STMicroelectronics, VL53L1X-Datasheet (st.com): ROI-/FoV-Tabelle, Mindestmessdistanz 4 cm
- Labsphere, Spectralon Diffuse Reflectance Standards (labsphere.com): PTFE-Basis, >99 % Remission 400–1500 nm, Lambert-Verhalten
- Sharp GP2Y0A51SK0F/GP2Y0A41SK0F-Datenblätter (global.sharp)

---

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
