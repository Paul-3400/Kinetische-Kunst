# -*- coding: utf-8 -*-
"""
Ball & Beam mit PID-Regler – Simulation mit PTFE-Vollkugel
=================================================================

Strecke:  Der Ball rollt auf einer ~350 mm langen Schiene (Balken).
          Ein Servo neigt den Balken um den Winkel theta; die Schwerkraft
          beschleunigt den Ball entlang der Schiene. Ohne Regelung rollt
          der Ball immer weg -> die Strecke ist instabil (Doppel-Integrator).

Physik (kleine Winkel):  r'' = K * sin(theta_absolut)
          K = 5/7 * g fuer Vollkugeln (PTFE-Kugel 35 mm, bestellt).
          Hohlkugel (Ping-Pong) waere 0.6 * g. In der Praxis K einmessen!

Fundament: Nur der ABSOLUTE Balkenwinkel zaehlt. Zwei Stoerungen:
          - Neigen des Fundaments um phi:  r'' = K * sin(theta + phi)
          - Fahren mit Beschleunigung a:   wirkt wie Zusatzneigung a/g,
            also r'' = K * (sin(theta+phi) - (a/g)*cos(theta+phi)).
          Gleichfoermige Fahrt stoert NICHT (Galilei), nur Anfahren/Bremsen.

Regler:   Diskreter PID mit
            - D-Anteil auf der MESSUNG (kein D-Kick beim Sollwertsprung)
            - Tiefpass auf dem D-Anteil (Sensorrauschen unterdruecken)
            - Anti-Windup (I-Anteil begrenzt; liefert max. Ki*I_MAX
              an statischer Fundament-Gegenneigung)
            - Ausgangsbegrenzung (max. Balkenwinkel)
          Zustzlich optional: Stoergrossen-Aufschaltung (Feedforward)
          theta_ff = arctan(a/g) fuer das Fahren.

Getestete Startwerte (PTFE-Kugel, +/-2 mm Rauschen):
          Ueberschwingen ca. 5 mm, eingeschwungen in < 2 s.

Laeuft ohne Zusatzpakete in Thonny; matplotlib ist optional.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 24.10.2026
"""

import math
import random

# ----------------------------------------------------------------------
# Konfiguration
# ----------------------------------------------------------------------
G = 9.81                        # Erdbeschleunigung (m/s^2)
K_STRECKE = (5 / 7) * G         # Vollkugel (PTFE); Hohlkugel: 0.6 * G
DT = 0.02                       # Abtastzeit 20 ms -> 50 Hz (passt zum VL53L1X)
DAUER_S = 16.0                  # Simulationsdauer (s)

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

# --- Fundament-Modus: Neigen ------------------------------------------
FUNDAMENT_NEIGUNG_GRAD = 0.0     # statische Fundament-Neigung (Kippachse)
FUNDAMENT_WIPPEN_AMPL_GRAD = 0.0  # Amplitude sinusfoermiges Wippen
FUNDAMENT_WIPPEN_HZ = 0.5        # Wippfrequenz

# --- Fundament-Modus: Fahren -------------------------------------------
FAHREN_A = 0.0                   # Fundament-Beschleunigung (m/s^2)
FAHREN_ANFAHREN_S = 2.0          # Dauer des Anfahrens (Trapez-Profil)
FAHREN_KONSTANT_S = 3.0          # Dauer der Konstantfahrt
FEEDFORWARD = True               # Stoergrossen-Aufschaltung arctan(a/g)


# ----------------------------------------------------------------------
# Fundament-Stoerungen (Zeitverlauf)
# ----------------------------------------------------------------------
def fundament_neigung(t):
    """Fundament-Neigung phi(t) in rad: statisch + sinusfoermiges Wippen."""
    phi = math.radians(FUNDAMENT_NEIGUNG_GRAD)
    if FUNDAMENT_WIPPEN_AMPL_GRAD > 0:
        phi += (math.radians(FUNDAMENT_WIPPEN_AMPL_GRAD)
                * math.sin(2 * math.pi * FUNDAMENT_WIPPEN_HZ * t))
    return phi


def fundament_beschleunigung(t):
    """Trapez-Fahrprofil: stehen -> anfahren -> konstant -> bremsen."""
    if FAHREN_A == 0.0:
        return 0.0
    start = 3.0                                   # losfahren bei t = 3 s
    t1 = start + FAHREN_ANFAHREN_S
    t2 = t1 + FAHREN_KONSTANT_S
    t3 = t2 + FAHREN_ANFAHREN_S
    if t < start:
        return 0.0
    if t < t1:
        return FAHREN_A                           # anfahren
    if t < t2:
        return 0.0                                # Konstantfahrt (Galilei!)
    if t < t3:
        return -FAHREN_A                          # bremsen
    return 0.0                                    # stehen


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
# Simulation der Strecke (Servo + rollender Ball + Fundament)
# ----------------------------------------------------------------------
class BallUndBalken:
    """Simuliert Servo (Drehzahlbegrenzung) und rollenden Ball."""

    def __init__(self, r0, rauschen_mm=0.0, seed=42):
        self.r = r0                 # wahre Ballposition (m)
        self.v = 0.0                # Ballgeschwindigkeit (m/s)
        self.theta = 0.0            # Balkenwinkel relativ zum Fundament (rad)
        self.rauschen = rauschen_mm / 1000.0
        self.rng = random.Random(seed)

    def messen(self):
        """Verrauschte Messung (ToF-Sensor sitzt auf der Schiene)."""
        return self.r + (self.rng.random() - 0.5) * 2 * self.rauschen

    def schritt(self, theta_soll, dt, phi=0.0, a_fundament=0.0):
        # Servo: begrenzte Drehgeschwindigkeit
        d_theta = max(-SERVO_RATE, min(SERVO_RATE,
                                       (theta_soll - self.theta) / dt))
        self.theta += d_theta * dt
        # Physik: nur der ABSOLUTE Winkel zaehlt; Fundamentbeschleunigung
        # wirkt wie eine Zusatzneigung a/g
        beschl = K_STRECKE * (math.sin(self.theta + phi)
                              - (a_fundament / G) * math.cos(self.theta + phi))
        self.v += beschl * dt
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
    max_abw_mm = 0.0                # max. Abweichung ab t = 1 s (Stoerungs-Mass)

    for i in range(int(DAUER_S / DT)):
        t = i * DT
        phi = fundament_neigung(t)                 # Fundament-Neigung
        a_f = fundament_beschleunigung(t)          # Fundament-Beschleunigung

        mess = strecke.messen()
        theta_soll = regler.schritt(R_SOLL, mess)   # -> Balkenwinkel
        if FEEDFORWARD and a_f != 0.0:
            # Stoergrossen-Aufschaltung: Schiene praeventiv dagegen kippen
            theta_soll = max(-THETA_MAX,
                             min(THETA_MAX, theta_soll + math.atan(a_f / G)))
        strecke.schritt(theta_soll, DT, phi, a_f)

        # Kennzahlen (auf wahrer Position, nicht auf der Messung)
        if t > 1.0:
            max_abw_mm = max(max_abw_mm, abs(strecke.r - R_SOLL) * 1000)
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
        "max_abweichung_mm": round(max_abw_mm, 1),
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
    print("Ball & Beam – PID-Regelsimulation (PTFE-Vollkugel)")
    print("=" * 62)
    print(f"Strecke: K = {K_STRECKE:.2f} m/s^2 pro rad,"
          f" Balken max. +/-{math.degrees(THETA_MAX):.0f} Grad")
    print(f"Regler:  Kp={KP}, Ki={KI}, Kd={KD},"
          f" Abtastzeit {DT * 1000:.0f} ms ({1 / DT:.0f} Hz)")
    print(f"Spiel:   Start {R_START * 100:.0f} cm ->"
          f" Soll {R_SOLL * 100:.0f} cm,"
          f" Sensorrauschen +/-{RAUSCHEN_MM:.0f} mm")
    print(f"Fundament: statisch {FUNDAMENT_NEIGUNG_GRAD:.1f} Grad,"
          f" Wippen {FUNDAMENT_WIPPEN_AMPL_GRAD:.1f} Grad"
          f" @ {FUNDAMENT_WIPPEN_HZ:.1f} Hz")
    print(f"Fahren:   {FAHREN_A:.2f} m/s^2 (Trapez),"
          f" Feedforward {'an' if FEEDFORWARD else 'aus'}")

    verlauf, stats = simuliere()

    ascii_verlauf(verlauf)
    print("\nKennzahlen:")
    print(f"  Ueberschwingen (nach 1. Ueberquerung): "
          f"{stats['ueberschwingen_mm']:.1f} mm")
    print(f"  Max. Abweichung (ab t=1 s):            "
          f"{stats['max_abweichung_mm']:.1f} mm")
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
    print("  - Konfig. B (Drehpunkt am Ende): THETA_MAX=radians(2.8),")
    print("    SERVO_RATE=1.0 und Kp=10, Ki=1, Kd=4 -> ~8 mm, ~3.2 s.")
    print("  - Fundament statisch: FUNDAMENT_NEIGUNG_GRAD = 1 / 2 / 3")
    print("    -> Grenze liegt bei knapp unter dem Winkelvorrat!")
    print("  - Fundament wippend: AMPL=0.5, HZ=0.5 oder 2.0 -> harmlos.")
    print("  - Fahren: FAHREN_A=0.3, FEEDFORWARD an/aus vergleichen.")
    plot_verlauf(verlauf)


if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------
# Hardware-Skelett (auskommentiert) – Echtbetrieb am Raspberry Pi
# ----------------------------------------------------------------------
# Aufbau:  VL53L1X (ToF) fest am einen Schienenende, misst die Ballposition
#          entlang der Schiene (50-350 mm). Servo (z.B. MG90S, Metallgetriebe)
#          kippt die Schiene am anderen Ende.
# Optional: MPU6050-IMU am Balken -> ABSOLUTE Winkelmessung; innere
#          Kaskade regelt dann theta+phi und das System wird
#          neigungs-invariant (empfohlen bei geneigtem/wippendem Fundament).
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
