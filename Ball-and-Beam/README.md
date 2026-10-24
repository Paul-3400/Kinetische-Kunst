# Ball & Beam – PID-Regelung mit Ping-Pong-Ball

**Kinetisches Objekt und Regelungstechnik-Experiment in einem:** Ein Ping-Pong-Ball rollt auf einer rund 350 mm langen Schiene. Ein Servo kippt die Schiene, ein Laser-ToF-Sensor misst die Ballposition, und ein PID-Regler hält den Ball aktiv auf der Sollposition. Ohne Regelung rollt der Ball unweigerlich davon – die Strecke ist ein instabiler Doppel-Integrator und damit ein Klassiker der Regelungstechnik.

## Funktionsweise

- **Physik (kleine Winkel):** r'' = K · sin(θ) mit K ≈ 0.6 · g (Ping-Pong-Ball ≈ Hohlkugel; massive Kugel ≈ 5/7 · g ≈ 0.71 · g). K ist am echten Aufbau einzumessen (Kalibrierfahrt mit bekanntem Winkel). Der Drehpunkt (Mitte oder Ende) geht nicht in die Bewegungsgleichung ein – nur der Balkenwinkel zählt.
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

## Simulation (ball_and_beam_pid.py)

Reine Python-Simulation ohne Zusatzpakete (läuft direkt in Thonny; matplotlib optional). Ausgabe: ASCII-Verlauf der Ballposition und Kennzahlen (Überschwingen nach der ersten Sollwert-Überquerung, Einschwingzeit ±5 mm, Restfehler). Enthält ein auskommentiertes Hardware-Skelett für den Echtbetrieb am Raspberry Pi (VL53L1X, gpiozero + PiGPIOFactory, pigpiod).

Getestete Regler-Startwerte für Konfiguration A (bei ±2 mm simuliertem Sensorrauschen):

| Parameter | Wert |
|---|---|
| Kp | 4.0 |
| Ki | 0.5 |
| Kd | 1.2 |
| Abtastzeit | 20 ms (50 Hz) |
| max. Balkenwinkel | ±7° |

Ergebnis: Überschwingen ca. 5 mm, eingeschwungen in unter 1 s; robust bis ±5 mm Sensorrauschen (dann max. ca. 15 mm Überschwingen).

## Tuning-Rezept für den echten Aufbau

1. Ki = 0, Kd = 0: Kp erhöhen, bis der Ball kräftig zum Sollwert läuft, aber als Pendel schwingt.
2. Kd erhöhen, bis das Pendeln gedämpft ist (Hauptabgleich).
3. Ki vorsichtig erhöhen, bis der Reibungs-Restfehler verschwindet (10–20 % von Kp als Faustregel).
4. Bei Zittern: zuerst D-Filter stärker einstellen, dann Kd senken.

## Geplante Hardware

- 2× Alu-U-Profil oder Vorhangschienen-Paar als Schiene (~350 mm), Ball läuft gerade
- Drehpunkt am einen Schienenende, Heber (MG90S) am anderen Ende (Konfiguration B, siehe oben)
- Verlängerter Servoarm (~40 mm) oder Kurbel-Schubstange; Gegengewicht hinter dem Drehpunkt
- VL53L1X-Breakout (z. B. Pololu, Adafruit oder SparkFun), auf der Schiene am Drehpunkt-Ende
- Raspberry Pi mit I²C, gpiozero + pigpiod

## Quellen

- Control Tutorials for MATLAB and Simulink – Ball & Beam: System Modeling und PID Controller Design (ctms.engin.umich.edu)
- STMicroelectronics, VL53L1X-Datasheet (st.com)
- Sharp GP2Y0A51SK0F/GP2Y0A41SK0F-Datenblätter (global.sharp)

---

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
