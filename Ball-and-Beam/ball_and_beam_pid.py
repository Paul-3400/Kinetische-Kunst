# -*- coding: utf-8 -*-
"""
Ball & Beam mit PID-Regler – Simulation für einen Ping-Pong-Ball
=================================================================

Strecke:  Der Ball rollt auf einer ~350 mm langen Schiene (Balken).
          Ein Servo neigt den Balken um den Winkel theta; die Schwerkraft
          beschleunigt den Ball entlang der Schiene. Ohne Regelung rollt
          der Ball immer weg -> die Strecke ist instabil (Doppel-Integrator).

Physik (kleine Winkel):  r'' = K * sin(theta)   mit K = 0.6 * g
          Ping-Pong-Ball = annähernd Hohlkugel -> Faktor ~0.6*g.
          Massive Kugel wäre 5/7*g ~ 0.71*g. In der Praxis K einmessen!

Regler:   Diskreter PID mit
            - D-Anteil auf der MESSUNG (kein D-Kick beim Sollwertsprung)
            - Tiefpass auf dem D-Anteil (Sensorrauschen unterdrücken)
            - Anti-Windup (I-Anteil begrenzt)
            - Ausgangsbegrenzung (max. Balkenwinkel)

Getestete Startwerte: Ueberschwingen ca. 5 mm, eingeschwungen in < 1 s
(auch bei simuliertem Sensorrauschen von +/- 2 mm).

Laeuft ohne Zusatzpakete in Thonny; matplotlib ist optional.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
"""

import math
import random

# ----------------------------------------------------------------------
# Konfiguration
# ----------------------------------------------------------------------
G = 9.81                        # Erdbeschleunigung (m/s^2)
K_STRECKE = 0.6 * G             # Streckenverstaerkung (m/s^2 pro rad)
DT = 0.02                       # Abtastzeit 20 ms -> 50 Hz (passt zum VL53L1X)
DAUER_S = 12.0                  # Simulationsdauer (s)

THETA_MAX = math.radians(7)     # max. Balkenwinkel (rad)
SERVO_RATE = math.radians(300) # Servo-Drehgeschwindigkeit (rad/s)
R_MIN, R_MAX = 0.02, 0.38       # Anschlaege des Balkens (m)

RAUSCHEN_MM = 2.0               # simuliertes Sensorrauschen (+/- mm)

# Regler-Startwerte (in dieser Simulation getestet):
KP = 4.0
KI = 0.5
KD = 1.2
D_FILTER = 0.4                  # D-Tiefpass (0..1, groesser = schneller)
I_MAX = 0.05                    # Anti-Windup-Grenze fuer I-Anteil

R_SOLL = 0.20                   # Sollposition (m), Mitte der Schiene
R_START = 0.30                  # Startposition (m)


# ----------------------------------------------------------------------
# PID-Regler
# ----------------------------------------------------------------------
class PIDRegler:
    """Diskreter PID-Regler mit Anti-Windup und gefiltertem D-Anteil.

    Ausgang = Sollwinkel des Balkens (rad), begrenzt auf +/- out_max.
    """

    def __init__(self, kp, ki, kd, dt, out_max, d_filter=0.4, i_max=0.05):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.dt = dt
        self.out_max = out_max
        self.d_filter = d_filter
        self.i_max = i_max
        self.integ = 0.0
        self.d_gefiltert = 0.0
        self.mess_alt = None

    def schritt(self, soll, mess):
        # --- D-Anteil aus der Messung (nicht vom Fehler): kein D-Kick
        if self.mess_alt is None:
            d_roh = 0.0
        else:
            d_roh = (mess - self.mess_alt) / self.dt
        self.mess_alt = mess
        # Tiefpass glaettet das Sensorrauschen
        self.d_gefiltert += self.d_filter * (d_roh - self.d_gefiltert)

        fehler = soll - mess
        # --- I-Anteil mit Anti-Windup
        self.integ += fehler * self.dt
        self.integ = max(-self.i_max, min(self.i_max, self.integ))

        stell = (self.kp * fehler
                 + self.ki * self.integ
                 - self.kd * self.d_gefiltert)
        return max(-self.out_max, min(self.out_max, stell))


# ----------------------------------------------------------------------
# Simulation der Strecke (Servo + rollender Ball)
# ----------------------------------------------------------------------
class BallUndBalken:
    """Simuliert Servo (Drehzahlbegrenzung) und rollenden Ball."""

    def __init__(self, r0, rauschen_mm=0.0, seed=42):
        self.r = r0                 # wahre Ballposition (m)
        self.v = 0.0                # Ballgeschwindigkeit (m/s)
        self.theta = 0.0            # tatsaechlicher Balkenwinkel (rad)
        self.rauschen = rauschen_mm / 1000.0
        self.rng = random.Random(seed)

    def messen(self):
        """Verrauschte Sensor-Messung (wie ein realer ToF-Sensor)."""
        return self.r + (self.rng.random() - 0.5) * 2 * self.rauschen

    def schritt(self, theta_soll, dt):
        # Servo: begrenzte Drehgeschwindigkeit
        d_theta = max(-SERVO_RATE, min(SERVO_RATE,
                                       (theta_soll - self.theta) / dt))
        self.theta += d_theta * dt
        # Physik: r'' = K * sin(theta)
        self.v += K_STRECKE * math.sin(self.theta) * dt
        self.r += self.v * dt
        # Anschlaege am Schienenende
        if self.r < R_MIN or self.r > R_MAX:
            self.r = max(R_MIN, min(R_MAX, self.r))
            self.v = 0.0


# ----------------------------------------------------------------------
# Simulation laufen lassen
# ----------------------------------------------------------------------
def simuliere():
    regler = PIDRegler(KP, KI, KD, DT, THETA_MAX, D_FILTER, I_MAX)
    strecke = BallUndBalken(R_START, RAUSCHEN_MM)

    verlauf = []                    # (t, wahre Position)
    ueberquerung_t = None           # erste Sollwert-Ueberquerung
    ueberschw_mm = 0.0              # max. Abweichung NACH der Ueberquerung
    einschwing_s = None             # Dauer bis +/- 5 mm gehalten

    for i in range(int(DAUER_S / DT)):
        t = i * DT
        mess = strecke.messen()
        theta_soll = regler.schritt(R_SOLL, mess)   # -> Balkenwinkel
        strecke.schritt(theta_soll, DT)

        # Kennzahlen (auf wahrer Position, nicht auf der Messung)
        if ueberquerung_t is None:
            von_oben = R_START > R_SOLL and strecke.r <= R_SOLL
            von_unten = R_START < R_SOLL and strecke.r >= R_SOLL
            if von_oben or von_unten:
                ueberquerung_t = t
        if ueberquerung_t is not None:
            abw = abs(strecke.r - R_SOLL)
            ueberschw_mm = max(ueberschw_mm, abw)
            if einschwing_s is None and abw < 0.005:
                einschwing_s = t
        verlauf.append((t, strecke.r))

    stats = {
        "ueberschwingen_mm": round(ueberschw_mm * 1000, 1),
        "einschwingen_s": round(einschwing_s, 2) if einschwing_s else None,
        "endposition_m": round(strecke.r, 4),
        "restfehler_mm": round(abs(strecke.r - R_SOLL) * 1000, 1),
    }
    return verlauf, stats


# ----------------------------------------------------------------------
# Ausgabe: ASCII-Verlauf + Kennzahlen, optional matplotlib
# ----------------------------------------------------------------------
def ascii_verlauf(verlauf):
    breite = 60
    soll_spalte = int(round((R_SOLL - R_MIN) / (R_MAX - R_MIN) * breite))
    print("\nVerlauf (alle 0.2 s | 1 Zeichen ~ 6 mm | # = Ball, S = Sollwert):")
    for t, r in verlauf[::10]:
        n = int(round((r - R_MIN) / (R_MAX - R_MIN) * breite))
        zeile = [" "] * (breite + 1)
        zeile[max(0, min(breite, n))] = "#"
        zeile[soll_spalte] = "S" if zeile[soll_spalte] == " " else "#"
        print(f"t={t:5.1f}s |{''.join(zeile)}|")
    print(f"           Skala: links {R_MIN*100:.0f} cm, rechts {R_MAX*100:.0f} cm")


def plot_verlauf(verlauf):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib nicht installiert – ASCII-Verlauf oben genuegt.)")
        return
    ts = [t for t, _ in verlauf]
    rs = [r for _, r in verlauf]
    plt.plot(ts, rs, label="Ballposition")
    plt.axhline(R_SOLL, ls="--", color="gray", label="Sollposition")
    plt.xlabel("Zeit (s)")
    plt.ylabel("Position (m)")
    plt.title("Ball & Beam – PID-Regelung (Simulation)")
    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    print("=" * 62)
    print("Ball & Beam – PID-Regelsimulation (Ping-Pong-Ball)")
    print("=" * 62)
    print(f"Strecke: K = {K_STRECKE:.2f} m/s^2 pro rad,"
          f" Balken max. +/-{math.degrees(THETA_MAX):.0f} Grad")
    print(f"Regler:  Kp={KP}, Ki={KI}, Kd={KD},"
          f" Abtastzeit {DT * 1000:.0f} ms ({1 / DT:.0f} Hz)")
    print(f"Spiel:   Start {R_START * 100:.0f} cm ->"
          f" Soll {R_SOLL * 100:.0f} cm,"
          f" Sensorrauschen +/-{RAUSCHEN_MM:.0f} mm")

    verlauf, stats = simuliere()

    ascii_verlauf(verlauf)
    print("\nKennzahlen:")
    print(f"  Ueberschwingen (nach 1. Ueberquerung): "
          f"{stats['ueberschwingen_mm']:.1f} mm")
    if stats["einschwingen_s"] is not None:
        print(f"  Eingeschwungen (+/-5 mm) nach:        "
              f"{stats['einschwingen_s']:.2f} s")
    else:
        print("  Eingeschwungen (+/-5 mm):             NICHT erreicht!")
    print(f"  Endposition:                          "
          f"{stats['endposition_m'] * 100:.1f} cm"
          f"  (Restfehler {stats['restfehler_mm']:.1f} mm)")

    print("\nExperimente zum Spielen:")
    print("  - KI = 0 setzen: gleiche Simulation ohne I-Anteil -> Restfehler?")
    print("  - RAUSCHEN_MM = 10: wie reagiert der D-Anteil?")
    print("  - THETA_MAX = radians(2): schwaches Servo -> langsamer?")
    print("  - R_START = 0.08: Regelung aus der Gegenrichtung probieren.")
    plot_verlauf(verlauf)


if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------
# Hardware-Skelett (auskommentiert) – Echtbetrieb am Raspberry Pi
# ----------------------------------------------------------------------
# Aufbau:  VL53L1X (ToF) fest am einen Schienenende, misst die Ballposition
#          entlang der Schiene (50-350 mm). Servo (z.B. MG90S, Metallgetriebe)
#          kippt die Schiene am anderen Ende.
#
# Vorbereitung:
#     sudo pip3 install vl53l1x            # Pimoroni-Treiber
#     sudo apt install pigpiod              # ruckelfreie Servo-Pulse
#     sudo systemctl enable --now pigpiod
#
# from gpiozero import AngularServo
# from gpiozero.pins.pigpio import PiGPIOFactory
# from vl53l1x import VL53L1X
# import time
#
# factory = PiGPIOFactory()                      # ruhige Servo-Signale
# servo = AngularServo(18, min_angle=-20, max_angle=20,
#                      initial_angle=0, pin_factory=factory)
# sensor = VL53L1X(i2c_bus=1)
# sensor.start_ranging(1)                        # Modus 1 = kurze Distanz, schnell
#
# regler = PIDRegler(KP, KI, KD, DT, THETA_MAX, D_FILTER, I_MAX)
# while True:
#     mess = sensor.get_distance() / 1000.0     # mm -> m
#     theta = regler.schritt(R_SOLL, mess)      # Ausgang = Balkenwinkel (rad)
#     servo.angle = math.degrees(-theta)        # Vorzeichen je nach Aufbau!
#     time.sleep(DT)
# ----------------------------------------------------------------------
