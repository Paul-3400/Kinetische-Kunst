# Ball & Beam – PID-Regelung mit PTFE-Vollkugel

**Kinetisches Objekt und Regelungstechnik-Experiment in einem:** Eine PTFE-Vollkugel (35 mm, bestellt 24.10.2026) rollt auf einer rund 350 mm langen Schiene. Ein Servo kippt die Schiene, ein Laser-ToF-Sensor misst die Ballposition, und ein PID-Regler hält den Ball aktiv auf der Sollposition. Ohne Regelung rollt der Ball unweigerlich davon – die Strecke ist ein instabiler Doppel-Integrator und damit ein Klassiker der Regelungstechnik.

## Funktionsweise

- **Physik (kleine Winkel):** r'' = K · sin(θ) mit K ≈ 0.6 · g für Hohlkugeln (Ping-Pong) bzw. K = 5/7 · g ≈ 0.71 · g für Vollkugeln (PTFE, Golfball). Der Drehpunkt (Mitte oder Ende) geht nicht in die Bewegungsgleichung ein – nur der Balkenwinkel zählt. K ist am echten Aufbau einzumessen (Kalibrierfahrt mit bekanntem Winkel).
- **Sensor:** VL53L1X (Laser-ToF, I²C) fest am einen Schienenende; misst die Ballposition entlang der Schiene (ca. 50–350 mm) mit bis zu 50 Hz, ohne tote Zone, ROI einengbar. Ultraschall (HC-SR04) wurde bewusst verworfen: kleines kugelförmiges Ziel mit schwachem Echo, träger ~60-ms-Messzyklus. Alternative: Sharp GP2Y0A41SK0F (4–30 cm, analog, nichtlinear) oder Kamera + OpenCV bei bewegtem Ball.
- **Antrieb:** Servo MG90S (Metallgetriebe) kippt die Schiene, maximal ±7°.
- **Regler:** Diskreter PID-Regler mit 50 Hz Abtastzeit:
  - D-Anteil auf der Messung statt auf dem Fehler (kein «D-Kick» bei Sollwertsprüngen)
  - Tiefpass auf dem D-Anteil gegen Sensorrauschen
  - Anti-Windup (I-Anteil begrenzt) und Ausgangsbegrenzung (Balkenwinkel)

## Konstruktionsentscheide – Drehpunkt am Schienenende (Konfiguration B)

**Entscheid (24.10.2026):** Der Drehpunkt liegt am einen Schienenende, der Heber (Servo) greift am anderen Ende an («Wipp-/Kranprinzip»). Die Ball-Physik ändert sich dadurch nicht (weiterhin r'' = K · sin(θ)), wohl aber die Aktor-Geometrie:

| Eigenschaft | A: Drehpunkt Mitte, Heber am Ende | B: Drehpunkt Ende, Heber am Ende (gewählt) |
|---|---|---|
| Hebelarm des Hebers | ~175 mm | ~350 mm |
| Hubbedarf am Heber für ±7° | ±21 mm | ±42 mm |
| Max. Winkel mit 20-mm-Servoarm (±60°) | ~±5,5° | ~±2,8° |
| Winkel-Auflösung (0,1 mm Heberhub) | 0,57 mrad | 0,29 mrad (feiner) |
| Spiel am Heber (0,5 mm) → Winkelfehler | 1,6 mrad | 0,8 mrad (halber Fehler) |
| Kraft am Heber | ~Balgewicht | geringer (doppelter Hebel) |
| Schienengewicht um Drehpunkt | ausbalanciert | einseitig → Drehmoment |

**Eingegangene Konsequenzen und Massnahmen:**

1. **Servoarm verlängern:** Ein Standard-Servoarm (20 mm, ±60° ≈ ±17 mm Hub) erreicht in Konfiguration B nur ±2,8° Neigung – zu träge für gute Regelung. Geplant: Servoarm ~40 mm oder Kurbel-Schubstange für ±5–7°. Alternativ: Heber bei ~70 % der Schienenlänge angreifen lassen (weniger Hubbedarf, etwas mehr Kraft).
2. **Gegengewicht hinter dem Drehpunkt:** In Konfiguration B erzeugt das Schienengewicht ein permanentes Drehmoment (bei ~100 g Schiene ca. 0,17 N·m), das der Servo sonst dauerhaft hält (Brummen, Erwärmung, Holding-Jitter). Kleines Gegengewicht an einer 10–15 %-Verlängerung hinter dem Drehpunkt entlastet ihn.
3. **Sensor auf der Schiene montieren:** Der VL53L1X sitzt auf der Schiene am Drehpunkt-Ende und dreht mit – er misst dann die wahre Ballposition r. Starr am Rahmen montiert, sähe er nur die Projektion r · cos(θ) (bei ±7° bis ~2,6 mm winkelabhängiger Fehler). Am Drehpunkt bewegt er sich im Raum kaum, dreht aber korrekt mit.

**Reglerwerte für Konfiguration B** (Simulation, ±2,8°, Servo ~1 rad/s Balkenwinkelgeschwindigkeit): **Kp = 10, Ki = 1, Kd = 4** → Überschwingen ~8 mm, eingeschwungen in ~3,2 s (auch aus der Gegenrichtung stabil, dort ~20 mm Überschwingen). Die Werte für Konfiguration A (Kp = 4, Ki = 0.5, Kd = 1.2) sind mit dieser Geometrie zu weich (~28 mm Überschwingen).

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
| Sensor-Signal | ≥ 25 mm, komfortabel 30–40 mm | Fleckdeckung bei 350 mm: Volle FoV (27°) → ~168 mm Fleck; ROI 8×8 → ~123 mm; ROI 4×4 → ~92 mm. Bei 30 mm Kugel ≈ 10 %, bei 35 mm ≈ 14 %, bei 40 mm ≈ 19 % Deckung (ROI 4×4). Unter ~5 % Deckung wird die Wiederholgenauigkeit dünn (Aussetzer, Streuung); dank >99 % PTFE-Remission darf das ROI eng bleiben |
| Schienenführung | Durchmesser ≥ 1.2–1.5 × Schienenmittenabstand | Sonst sitzt die Kugel zu flach im «Tal» und läuft seitlich weg. Bei 35 mm Kugel → Schienenabstand ~23–29 mm, gewählt ~25 mm |
| Rolldynamik | ≥ 25 mm | Unempfindlichkeit gegen Schienen-Fugen und Rundheitstoleranzen; genügend Masse gegen Reibungseinflüsse |
| Sensor-Totzone | Ballfront nie näher als ~40 mm an den Sensor | Mindestmessdistanz des VL53L1X (4 cm) → mechanischer Anschlag entsprechend setzen |

**Sensoreinstellungen dazu:** ROI auf 4×4 oder 8×8 einengen und auf die Schienenachse zentrieren; Timing-Budget ~50 ms (Wiederholgenauigkeit vor Messrate – der Ball rollt langsam).

## Fundament-Einflüsse: Neigen und Fahren (24.10.2026)

**Physik:** Für den Ball zählt nur der *absolute* Balkenwinkel zur Horizontalen. Mit Fundament-Neigung φ und Fundament-Beschleunigung a (in Auslegerrichtung) gilt:

r'' = K · (sin(θ + φ) − (a/g) · cos(θ + φ))

Alle Fundament-Störungen sind damit dieselbe Währung – **additiver Winkel am Streckeneingang**:

| Störung | Äquivalent am Streckeneingang |
|---|---|
| Fahren mit Beschleunigung a | Δθ = a/g (1 m/s² ≡ 5,8°) |
| Statische Fundament-Neigung φ | Δθ = φ (1:1) |
| Wippen/Vibration (Amplitude A, Frequenz f) | Δθ = A·sin(ωt), bei höheren Frequenzen kaum wirksam |

**Neigen (statisch):** Der PID absorbiert die Neigung, indem der Servo dauerhaft einen Gegenwinkel hält – geliefert vom I-Anteil, der durch Anti-Windup auf Ki · I_MAX ≈ 2,9° begrenzt ist. Simulations-Ergebnisse (Konfiguration B, ±2,8°): 1° → unkritisch (~7 mm Einschwingen); 2° → Grenzbereich (~12 mm, Servo am Rand); **3° → Versagen**: Servo am Anschlag, der Ball läuft bis zum Schienenende. Toleranz ≈ Winkelbudget minus Regel-Reserve:

| Winkelvorrat | Max. statische Fundament-Neigung |
|---|---|
| ±2,8° (Standard-Servoarm) | ~2° |
| ±5,5° (40-mm-Arm) | ~4–4,5° |
| ±7° (Kurbel) | ~5,5–6° |

**Wippen (dynamisch):** Harmloser als statisch – 0,5° Amplitude (0,5 oder 2 Hz) gibt nur ~5–6 mm Abweichung; der Ball ist als träge Masse für schnelles Wippen unempfindlich. Statisch ist gefährlicher als dynamisch.

**Fahren:** Gleichförmige Fahrt stört nicht (Galilei-Invarianz), nur Anfahren/Bremsen (Δθ = a/g). Grenze: a_max = g · tan(θ_max) → 0,48 m/s² bei ±2,8°, ~1,2 m/s² bei ±7°. Massnahmen: Rampen statt Sprünge sowie **Störgrossen-Aufschaltung** θ_ff = arctan(a/g) (Simulation: 13 → 5 mm Auslenkung bei 0,3 m/s²). Damit ist die Skulptur grundsätzlich «fahrfähig» – Fundament als zweite Stellgrösse in einer Kaskade.

**Seitliche Neigung:** Anderer Modus, viel toleranter: Mit dem Schienen-Sattel (35-mm-Kugel, 25-mm-Mittenabstand) rollt die Kugel erst ab ~45° aus. Nur die Kippachse ist der empfindliche Modus.

**Drei Massnahmen gegen Fundament-Neigung (nach Aufwand):**

1. **Fundament mit Libelle waagrecht ausrichten** (einmalig beim Aufbau).
2. **I_MAX anheben**, wenn die Umgebung neigt (z. B. 0.05 → 0.12 rad·s erlaubt ~7° Bias) – sonst schlägt die Anti-Windup-Bremse knapp vor dem Servo-Limit zu.
3. **IMU (MPU6050, ~CHF 5) am Balken:** absoluten Winkel (θ+φ) messen und als innere Kaskade den *absoluten* Winkel regeln → das System wird neigungs-invariant. Die sauberste Lösung für kinetische Kunst.

## Simulation (ball_and_beam_pid.py)

Reine Python-Simulation ohne Zusatzpakete (läuft direkt in Thonny; matplotlib optional). Ausgabe: ASCII-Verlauf der Ballposition und Kennzahlen (Überschwingen, maximale Abweichung, Einschwingzeit ±5 mm, Restfehler). Enthält ein auskommentiertes Hardware-Skelett für den Echtbetrieb am Raspberry Pi (VL53L1X, gpiozero + PiGPIOFactory, pigpiod; optional MPU6050-IMU für absolute Winkelregelung).

Seit 24.10.2026 rechnet das Skript voreingestellt mit **K = 5/7 · g** (PTFE-Vollkugel); für eine Hohlkugel (Ping-Pong) `K_STRECKE = 0.6 * G` setzen.

**Fundament-Modus im Skript** (Umgebung simulieren, ohne den Regler zu ändern):

| Parameter | Wirkung |
|---|---|
| `FUNDAMENT_NEIGUNG_GRAD` | statische Fundament-Neigung in der Kippachse |
| `FUNDAMENT_WIPPEN_AMPL_GRAD` / `FUNDAMENT_WIPPEN_HZ` | sinusförmiges Wippen |
| `FAHREN_A`, `FAHREN_ANFAHREN_S`, `FAHREN_KONSTANT_S` | Trapez-Fahrprofil (anfahren → konstant → bremsen) |
| `FEEDFORWARD` | Störgrossen-Aufschaltung θ_ff = arctan(a/g) ein/aus |

Getestete Regler-Startwerte für Konfiguration A (bei ±2 mm simuliertem Sensorrauschen):

| Parameter | Wert |
|---|---|
| Kp | 4.0 |
| Ki | 0.5 |
| Kd | 1.2 |
| Abtastzeit | 20 ms (50 Hz) |
| max. Balkenwinkel | ±7° |

Ergebnis (PTFE-Kugel): Überschwingen ca. 5 mm, eingeschwungen in unter 2 s; robust bis ±5 mm Sensorrauschen.

## Tuning-Rezept für den echten Aufbau

1. Ki = 0, Kd = 0: Kp erhöhen, bis der Ball kräftig zum Sollwert läuft, aber als Pendel schwingt.
2. Kd erhöhen, bis das Pendeln gedämpft ist (Hauptabgleich).
3. Ki vorsichtig erhöhen, bis der Reibungs-Restfehler verschwindet (10–20 % von Kp als Faustregel).
4. Bei Zittern: zuerst D-Filter stärker einstellen, dann Kd senken.

## Geplante Hardware

- 2× Alu-U-Profil oder Vorhangschienen-Paar als Schiene (~350 mm), Mittenabstand ~25 mm
- **PTFE-Vollkugel 35 mm** (Ball-Entscheid, siehe oben; Schienenmittenabstand dazu ~25 mm)
- Drehpunkt am einen Schienenende, Heber (MG90S) am anderen Ende (Konfiguration B, siehe oben)
- Verlängerter Servoarm (~40 mm) oder Kurbel-Schubstange; Gegengewicht hinter dem Drehpunkt
- VL53L1X-Breakout (z. B. Pololu, Adafruit oder SparkFun), auf der Schiene am Drehpunkt-Ende; ROI 4×4/8×8, Timing ~50 ms
- Optional: MPU6050-IMU am Balken (absolute Winkelregelung, neigungs-invariant)
- Raspberry Pi mit I²C, gpiozero + pigpiod

## Quellen

- Control Tutorials for MATLAB and Simulink – Ball & Beam: System Modeling und PID Controller Design (ctms.engin.umich.edu)
- STMicroelectronics, VL53L1X-Datasheet (st.com): ROI-/FoV-Tabelle, Mindestmessdistanz 4 cm
- Labsphere, Spectralon Diffuse Reflectance Standards (labsphere.com): PTFE-Basis, >99 % Remission 400–1500 nm, Lambert-Verhalten
- Sharp GP2Y0A51SK0F/GP2Y0A41SK0F-Datenblätter (global.sharp)

---

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
