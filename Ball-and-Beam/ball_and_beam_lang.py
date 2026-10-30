# -*- coding: utf-8 -*-
"""
Ball & Beam «lang» – PID-Regelsimulation mit Kurbelantrieb
=================================================================
Variante «lang» (650-mm-Balken, einseitig gelagert):

          NEMA17-Stepper
               |
          Scheibenrad (Kurbel, Bolzen auf Radius R)
               |   pendelnder Steigbuegel (Laenge ~L_z)
               v
   Drehpunkt —][ Balken liegt im Sattel des Buegels ......... Ball

Kinematik (Scotch-Crank mit Pendelentkopplung):
          sin(theta) = (R / L_z) * sin(alpha)
          theta = Balkenwinkel, alpha = Kurbelwinkel des Steppers,
          R = Bohrradius (Bolzen), L_z = Abstand Angriffspunkt<->Drehpunkt.

WICHTIGE ERKENNTNIS (Update 30.10.2026): Die Uebertragung ist NICHT
konstant!  dtheta/dalpha = (R/L_z) * cos(alpha) / cos(theta)
- bei alpha = 0 (Balken waagrecht): maximale Feinheit  ~R/L_z
- bei alpha = ±90° (Balken am Anschlag): dtheta/dalpha -> 0, der
  Balken "steht" fast still, waehrend die Kurbel eilig weiterlaeuft.
Eine Balken-Umkehr von -theta_max nach +theta_max erfordert einen
KURBELSCHWUNG VON 180 GRAD!  Zeit dafuer = pi / ALPHA_RATE.
Bei zu kleiner Kurbelrate wird der Regelkreis dadurch instabil
(Grenzzyklus zwischen den Anschlaegen) – die alte Naeherung
"slew = Kurbelrate * R/L_z" hat das unterschaetzt.

Regler-Empfehlung aus dieser Simulation (R=73 mm, L_z=600 mm,
±7° konstruktiv, Reglerbereich ±5° Reserve):
          Kp=3, Ki=0.5, Kd=1.5, Kurbelrate >= 720°/s (2 U/s)
          -> Ueberschwingen ~10 mm, eingeschwungen ~1.5 s
          (robust ueber Startpositionen 0.12–0.55 m und Saaten)

Fundament: wie in der Kompakt-Simulation – nur der ABSOLUTE
Balkenwinkel zaehlt; Neigung phi und Fahr-Beschleunigung a
wirken als additive Stoerwinkel am Streckeneingang.

Laeuft ohne Zusatzpakete in Thonny; matplotlib ist optional.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 30.10.2026
"""

import math
import random

# ----------------------------------------------------------------------
# Konfiguration – Geometrie der Langvariante
# ----------------------------------------------------------------------
G = 9.81                        # Erdbeschleunigung (m/s^2)
K_STRECKE = (5 / 7) * G         # Vollkugel (PTFE 35 mm); Hohlkugel: 0.6*G
DT = 0.02                       # Abtastzeit 20 ms -> 50 Hz
DAUER_S = 16.0                   # Simulationsdauer (s)

R_MIN, R_MAX = 0.05, 0.62        # Ball-Anschlaege (m): 50–600 mm
R_BOHR = 0.073                   # Bohrradius des Kurbelrads (m)
L_Z = 0.60                       # Abstand Angriffspunkt <-> Drehpunkt (m)
UEBER = R_BOHR / L_Z             # Uebersetzungs-Mass sin(7°) ≈ 0.122
THETA_KONSTR = math.asin(UEBER)  # konstruktiv moeglicher Balkenwinkel ±7.0°

# --- Antrieb: NEMA17-Stepper + Kurbel + Pendelbuegel --------------------
ALPHA_RATE = 4.0 * math.pi       # Kurbel-Winkelgeschwindigkeit (rad/s)
                                 # 4*pi = 720°/s = 2 U/s -> Mindestempfehlung!
USTEPS = 3200                    # Mikroschritte pro Umdrehung (16x)
USTEP_WINKEL = 2.0 * math.pi / USTEPS   # 0.1125° pro Mikroschritt
THETA_REGLER_GRAD = 5.0          # Regler nutzt nur ±5°, Rest = Reserve
THETA_LIMIT = min(THETA_KONSTR, math.radians(THETA_REGLER_GRAD))

# --- Sensor --------------------------------------------------------------
RAUSCHEN_MM = 4.0                # ±4 mm (lang: kleiner Fleck bei 600 mm)
MEDIAN_FILTER = True             # Median ueber 3 Messungen (VL53L1X)

# --- Regler --------------------------------------------------------------
KP = 3.0
KI = 0.5
KD = 1.5
D_FILTER = 0.2                   # D-Tiefpass (0..1, kleiner = ruhiger)
I_MAX = 0.05                     # Anti-Windup-Grenze (Ki*I_MAX ≈ 1.4°)

R_SOLL = 0.30                    # Sollposition (m), vorne = kleine Werte
R_START = 0.55                   # Startposition (m), grosse Fahrt nach vorn

# --- Fundament-Modus: Neigen -------------------------------------------
FUNDAMENT_NEIGUNG_GRAD = 0.0      # statische Fundament-Neigung (Kippachse)
FUNDAMENT_WIPPEN_AMPL_GRAD = 0.0  # Amplitude sinusfoermiges Wippen
FUNDAMENT_WIPPEN_HZ = 0.5         # Wippfrequenz

# --- Fundament-Modus: Fahren --------------------------------------------
FAHREN_A = 0.0                    # Fundament-Beschleunigung (m/s^2)
FAHREN_ANFAHREN_S = 2.0           # Dauer des Anfahrens (Trapez-Profil)
FAHREN_KONSTANT_S = 3.0           # Dauer der Konstantfahrt
FEEDFORWARD = True                # Stoergrossen-Aufschaltung arctan(a/g)


# ----------------------------------------------------------------------
# Fundament-Stoerungen (Zeitverlauf) – identisch zur Kompakt-Simulation
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
# Kurbel-Kinematik
# ----------------------------------------------------------------------
def theta_to_alpha(theta):
    """Balkenwinkel (rad) -> Kurbelwinkel (rad) via sin-Gesetz."""
    s = min(1.0, abs(math.sin(theta)) / UEBER)   # bei theta > theta_konstr
    vorzeichen = 1.0 if theta >= 0 else -1.0       # wird geclampt
    return vorzeichen * math.asin(s)


def umkehrzeit_s():
    """Zeit fuer die Balken-Umkehr -theta_max -> +theta_max (Vollast)."""
    return math.pi / ALPHA_RATE          # Kurbel muss 180° schwingen


# ----------------------------------------------------------------------
# PID-Regler – identisch zur Kompakt-Simulation
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
        # --- D-Anteil aus der Messung (kein D-Kick)
        if self.mess_alt is None:
            d_roh = 0.0
        else:
            d_roh = (mess - self.mess_alt) / self.dt
        self.mess_alt = mess
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
# Simulation der Strecke (Stepper-Kurbel + Pendelbuegel + Ball)
# ----------------------------------------------------------------------
class KurbelBalken:
    """NEMA17 mit Kurbelrad; Balken liegt im pendelnden Steigbuegel."""

    def __init__(self, r0, rauschen_mm=0.0, seed=42):
        self.r = r0                 # wahre Ballposition (m)
        self.v = 0.0                # Ballgeschwindigkeit (m/s)
        self.alpha = 0.0            # Kurbelwinkel des Steppers (rad)
        self.rauschen = rauschen_mm / 1000.0
        self.rng = random.Random(seed)
        self.fenster = []           # Median-Puffer (3 Messungen)

    def messen(self):
        """Verrauschte Messung (VL53L1X), optional Median ueber 3 Werte."""
        roh = self.r + (self.rng.random() - 0.5) * 2 * self.rauschen
        if MEDIAN_FILTER:
            self.fenster.append(roh)
            if len(self.fenster) > 3:
                self.fenster.pop(0)
            if len(self.fenster) == 3:
                return sorted(self.fenster)[1]
        return roh

    def schritt(self, theta_soll, dt, phi=0.0, a_fundament=0.0):
        # Stepper: Kurbelwinkel rate-begrenzt, dann auf Mikroschritte
        # quantisiert (der echte Zaehler kann nur ganze uSteps)
        alpha_soll = theta_to_alpha(theta_soll)
        d_alpha = max(-ALPHA_RATE, min(ALPHA_RATE,
                                      (alpha_soll - self.alpha) / dt))
        neu = self.alpha + d_alpha * dt
        self.alpha = round(neu / USTEP_WINKEL) * USTEP_WINKEL

        # Balkenwinkel folgt der Kurbelkinematik (sin-Gesetz)
        theta = math.asin(min(1.0, UEBER * math.sin(self.alpha)))

        # Physik: nur der ABSOLUTE Winkel zaehlt
        beschl = K_STRECKE * (math.sin(theta + phi)
                             - (a_fundament / G) * math.cos(theta + phi))
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
    regler = PIDRegler(KP, KI, KD, DT, THETA_LIMIT, D_FILTER, I_MAX)
    strecke = KurbelBalken(R_START, RAUSCHEN_MM)

    verlauf = []                    # (t, wahre Position)
    ueberquerung_t = None           # erste Sollwert-Ueberquerung
    ueberschw_mm = 0.0              # max. Abweichung NACH der Ueberquerung
    einschwing_s = None             # Dauer bis +/- 5 mm gehalten
    max_abw_mm = 0.0                # max. Abweichung ab t = 1 s

    for i in range(int(DAUER_S / DT)):
        t = i * DT
        phi = fundament_neigung(t)                 # Fundament-Neigung
        a_f = fundament_beschleunigung(t)          # Fundament-Beschl.

        mess = strecke.messen()
        theta_soll = regler.schritt(R_SOLL, mess)   # -> Balkenwinkel
        if FEEDFORWARD and a_f != 0.0:
            theta_soll = max(-THETA_LIMIT,
                             min(THETA_LIMIT,
                                 theta_soll + math.atan(a_f / G)))
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
    print("\nVerlauf (alle 0.2 s | 1 Zeichen ~ 10 mm | # = Ball, S = Sollwert):")
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
    plt.title("Ball & Beam «lang» – Kurbel/Stepper-Simulation")
    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    print("=" * 62)
    print("Ball & Beam «lang» – Kurbel/Stepper-Simulation")
    print("=" * 62)
    print(f"Geometrie: Bohrradius {R_BOHR*1000:.0f} mm, L_z = {L_Z*1000:.0f} mm"
          f" -> konstruktiv ±{math.degrees(THETA_KONSTR):.1f}°")
    print(f"Antrieb:  Kurbelrate {math.degrees(ALPHA_RATE):.0f}°/s"
          f" ({ALPHA_RATE/(2*math.pi):.1f} U/s), {USTEPS} uSteps/U")
    print(f"          Aufloesung: {UEBER*USTEP_WINKEL*1000:.2f} mrad/uStep,"
          f" Balken-Umkehr (voll) in {umkehrzeit_s():.2f} s")
    print(f"Regler:   Bereich ±{THETA_REGLER_GRAD:.0f}° (Reserve bis"
          f" ±{math.degrees(THETA_KONSTR):.0f}°),"
          f" Kp={KP}, Ki={KI}, Kd={KD}")
    print(f"Spiel:    Start {R_START*100:.0f} cm -> Soll {R_SOLL*100:.0f} cm,"
          f" Rauschen ±{RAUSCHEN_MM:.0f} mm,"
          f" Median {'an' if MEDIAN_FILTER else 'aus'}")
    print(f"Fundament: statisch {FUNDAMENT_NEIGUNG_GRAD:.1f}°,"
          f" Wippen {FUNDAMENT_WIPPEN_AMPL_GRAD:.1f}°"
          f" @ {FUNDAMENT_WIPPEN_HZ:.1f} Hz, Fahren {FAHREN_A:.2f} m/s²")

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
    print("  - ALPHA_RATE = 2*math.pi  -> halbe Kurbelrate: Grenzzyklus!")
    print("    (Die Balken-Umkehr braucht 180° Kurbelschwung – das ist")
    print("    DIE Lektion dieser Simulation: Kurbelrate >= 720°/s.)")
    print("  - R_BOHR = 0.040 -> nur ±3.8°: deutlich traeger (~45–70 mm).")
    print("  - THETA_REGLER_GRAD = 7.0 -> voller Bereich: Umkehr-")
    print("    schwung bis 180°, mehr Ueberschwingen. Reserve zahlt sich aus.")
    print("  - MEDIAN_FILTER = False -> D-Anteil zuckt bei ±4 mm Rauschen.")
    print("  - Kp=4, Kd=2 (D_FILTER 0.2): schneller, aber empfindlicher.")
    print("  - R_START = 0.12: grosse Fahrt von unten zur Mitte.")
    print("  - Fundament: FUNDAMENT_NEIGUNG_GRAD = 1 / 2 -> I-Anteil hebt.")
    print("  - Wippen: AMPL=0.5, HZ=0.5 / Fahren: FAHREN_A=0.3, FF an/aus.")
    plot_verlauf(verlauf)


if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------
# Hardware-Skelett (auskommentiert) – Echtbetrieb am Raspberry Pi
# ----------------------------------------------------------------------
# Aufbau:  NEMA17-Stepper mit angeflanschtem Kurbelrad (Bohrkreis bis
#          ~75 mm, Bolzen auf Radius R). Pendelnder Steigbuegel, Balken
#          liegt im Sattel (+ Niederhalter gegen Ausheben). Treiber:
#          TMC2209 (leise, 16 Mikroschritte -> 3200 uSteps/U) am RPi:
#          DIR- und STEP-Pin, ENA auf GND (aktiv low). VREF so einstellen,
#          dass der Motormaximalstrom nicht ueberschritten wird (NEMA17
#          je nach Typ 0.4–1.7 A; kleiner Motor genuegt, die Last ist
#          minimal: ~0.2 N·m Ballgewicht + Reibung).
# Homing:  Referenz-/Endlagenschalter bei alpha = 0 (Balken waagrecht)
#          -> nach jedem Einschalten 0-fahren, dann erst regeln.
#          Alternativ MPU6050 am Balken (absolute Winkelmessung).
# Sensor:  VL53L1X am Drehpunkt-Ende, ROI 4x4 auf die Schienenachse,
#          Timing ~50 ms (bei 600 mm kleiner Fleck -> Median-Filter,
#          wie in der Simulation MEDIAN_FILTER). Totzone: Ballfront
#          nicht naeher als ~40 mm an den Sensor -> R_MIN = 50 mm.
#
# Vorbereitung:
#     sudo pip3 install vl53l1x            # Pimoroni-Treiber
#
# from gpiozero import DigitalOutputDevice
# from vl53l1x import VL53L1X
# import time
#
# step = DigitalOutputDevice(20)          # STEP-Pin TMC2209
# richt = DigitalOutputDevice(21)         # DIR-Pin TMC2209
# sensor = VL53L1X(i2c_bus=1)
# sensor.start_ranging(1)                 # Modus 1 = kurz, schnell
#
# regler = PIDRegler(KP, KI, KD, DT, THETA_LIMIT, D_FILTER, I_MAX)
# while True:
#     mess = sensor.get_distance() / 1000.0        # mm -> m
#     theta_soll = regler.schritt(R_SOLL, mess)     # Balkenwinkel (rad)
#     alpha_soll = theta_to_alpha(theta_soll)      # -> Kurbelwinkel
#     d_alpha = alpha_soll - alpha_ist             # Zaehlerstand pflegen
#     n_usteps = int(d_alpha / USTEP_WINKEL)       # Mikroschritte fahren
#     richt.value = d_alpha >= 0
#     for _ in range(abs(n_usteps)):
#         step.on(); time.sleep(2e-5); step.off(); time.sleep(2e-5)
#     time.sleep(DT)                               # Schrittimpulse ggf.
#                                                  # per Hardware-PWM
# ----------------------------------------------------------------------

