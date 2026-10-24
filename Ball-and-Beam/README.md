# Ball & Beam – PID-Regelung mit Ping-Pong-Ball

**Kinetisches Objekt und Regelungstechnik-Experiment in einem:** Ein Ping-Pong-Ball rollt auf einer rund 350 mm langen Schiene. Ein Servo kippt die Schiene, ein Laser-ToF-Sensor misst die Ballposition, und ein PID-Regler hält den Ball aktiv auf der Sollposition. Ohne Regelung rollt der Ball unweigerlich davon – die Strecke ist ein instabiler Doppel-Integrator und damit ein Klassiker der Regelungstechnik.

## Funktionsweise

- **Physik (kleine Winkel):** r'' = K · sin(θ) mit K ≈ 0.6 · g (Ping-Pong-Ball ≈ Hohlkugel; massive Kugel ≈ 5/7 · g ≈ 0.71 · g). K ist am echten Aufbau einzumessen (Kalibrierfahrt mit bekanntem Winkel).
- **Sensor:** VL53L1X (Laser-ToF, I²C) fest am einen Schienenende; misst die Ballposition entlang der Schiene (ca. 50–350 mm) mit bis zu 50 Hz, ohne tote Zone, ROI einengbar. Ultraschall (HC-SR04) wurde bewusst verworfen: kleines kugelförmiges Ziel mit schwachem Echo, träger ~60-ms-Messzyklus. Alternative: Sharp GP2Y0A41SK0F (4–30 cm, analog, nichtlinear) oder Kamera + OpenCV bei bewegtem Ball.
- **Antrieb:** Servo MG90S (Metallgetriebe) kippt die Schiene um ihren Mittelpunkt, maximal ±7°.
- **Regler:** Diskreter PID-Regler mit 50 Hz Abtastzeit:
  - D-Anteil auf der Messung statt auf dem Fehler (kein «D-Kick» bei Sollwertsprüngen)
  - Tiefpass auf dem D-Anteil gegen Sensorrauschen
  - Anti-Windup (I-Anteil begrenzt) und Ausgangsbegrenzung (Balkenwinkel)

## Simulation (ball_and_beam_pid.py)

Reine Python-Simulation ohne Zusatzpakete (läuft direkt in Thonny; matplotlib optional). Ausgabe: ASCII-Verlauf der Ballposition und Kennzahlen (Überschwingen nach der ersten Sollwert-Überquerung, Einschwingzeit ±5 mm, Restfehler). Enthält ein auskommentiertes Hardware-Skelett für den Echtbetrieb am Raspberry Pi (VL53L1X, gpiozero + PiGPIOFactory, pigpiod).

Getestete Regler-Startwerte (bei ±2 mm simuliertem Sensorrauschen):

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
- VL53L1X-Breakout (z. B. Pololu, Adafruit oder SparkFun)
- MG90S-Servo
- Raspberry Pi mit I²C, gpiozero + pigpiod

## Quellen

- Control Tutorials for MATLAB and Simulink – Ball & Beam: System Modeling und PID Controller Design (ctms.engin.umich.edu)
- STMicroelectronics, VL53L1X-Datasheet (st.com)
- Sharp GP2Y0A51SK0F/GP2Y0A41SK0F-Datenblätter (global.sharp)

---

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
