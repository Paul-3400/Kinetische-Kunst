#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gcode_wascher.py – säubert svg2gcode-Ausgabe für den Walldraw-Polargraphen.

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 29.10.2026

Warum dieses Skript?
Die Firmware WallDraw.ino versteht pro Zeile nur die Wörter X, Y und Z:
  - Z > 0   -> Stift heben (z. B. "G01 Z5")
  - Z <= 0  -> Stift senken (z. B. "G01 Z-1")
Alles andere wird ignoriert – und genau das ist der Haken:

  1. Kommentarzeilen wie ";svg#layer1 > path#..." enthalten zufällig
     X- oder Y-Buchstaben. Weil Walldraw die Zeile gross schreibt und nur
     nach X/Y/Z sucht, kann ein Kommentar als Bewegung fehlgelesen
     werden.  -> Kommentare müssen weg.
  2. svg2gcode erzeugt (je nach Einstellung) keine Stift-Befehle.
     Ohne Z-Befehle bleibt der Stift während der Eilgänge (G0) unten und
     zieht Verbindungslinien durchs Bild.  -> Z-Befehle einfügen.
  3. Zeilennummern (N123) und Prüfsummen (*45) sind ein Streaming-
     Protokoll für 3D-Drucker; Walldraw braucht sie nicht.
     -> entfernen (kleinere Datei).
  4. Vorschub (F300) wird ignoriert.  -> entfernen (kleinere Datei).

Optional: Zeichnung mit --zentrieren um die Home-Position (0|0) mittig
unter die Gondel legen.

Aufruf (Thonny oder Terminal):
    python gcode_wascher.py eingabe.gcode ausgabe.nc
    python gcode_wascher.py eingabe.gcode ausgabe.nc --zentrieren

Tipp: als Ausgabe direkt "1.nc" angeben, dann die Datei auf die
FAT32-TF-Karte kopieren und loszeichnen.
"""

import argparse
import math
import re
import sys

# --- reguläre Ausdrücke ------------------------------------------------------
ZEILENNUMMER = re.compile(r"^N\d+\s*")
PRUEFSUMME = re.compile(r"\*\d+")
KOMMENTAR = re.compile(r";.*$")
VORSCHUB = re.compile(r"\s+F\d*\.?\d*\s*$")
EILGANG = re.compile(r"^G0*0\b")   # G0, G00
STRICH = re.compile(r"^G0*1\b")    # G1, G01
XY = re.compile(r"X(-?\d+\.?\d*)\s+Y(-?\d+\.?\d*)", re.IGNORECASE)

STIFT_HEBEN = "G01 Z5"    # Z > 0  -> Stift oben
STIFT_SENKEN = "G01 Z-1"  # Z <= 0 -> Stift unten


def saeubern(zeile):
    """Entfernt Kommentar, Zeilennummer, Prüfsumme und Vorschub."""
    z = KOMMENTAR.sub("", zeile)
    z = ZEILENNUMMER.sub("", z)
    z = PRUEFSUMME.sub("", z)
    z = VORSCHUB.sub("", z).strip()
    return z


def bbox(zeilen):
    """Liefert (xmin, xmax, ymin, ymax) aller X/Y-Koordinaten."""
    xs, ys = [], []
    for z in zeilen:
        m = XY.search(z)
        if m:
            xs.append(float(m.group(1)))
            ys.append(float(m.group(2)))
    if not xs:
        sys.exit("Fehler: keine X/Y-Koordinaten gefunden.")
    return min(xs), max(xs), min(ys), max(ys)


def waschen(eingabe_text, zentrieren):
    roh = [z.strip() for z in eingabe_text.splitlines() if z.strip()]
    sauber = [z for z in (saeubern(z) for z in roh) if z]

    xmin, xmax, ymin, ymax = bbox(sauber)
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0

    def verschieben(z):
        if not zentrieren:
            return z
        return XY.sub(
            lambda m: "X%.3f Y%.3f" % (float(m.group(1)) - cx,
                                      float(m.group(2)) - cy),
            z, count=1)

    ausgabe = []
    stift_oben = True          # Walldraw startet mit gehobenem Stift
    striche = 0
    for z in sauber:
        u = z.upper()
        if EILGANG.match(u):
            if not stift_oben:
                ausgabe.append(STIFT_HEBEN)
                stift_oben = True
            ausgabe.append(verschieben(z))
        elif STRICH.match(u):
            if stift_oben:
                ausgabe.append(STIFT_SENKEN)
                stift_oben = False
                striche += 1
            ausgabe.append(verschieben(z))
        else:                  # G21, G90 usw. – harmlos, durchreichen
            ausgabe.append(verschieben(z))
    if not stift_oben:
        ausgabe.append(STIFT_HEBEN)

    # Weglänge für die grobe Zeit-Schätzung
    laenge = 0.0
    letzter = None
    for z in sauber:
        m = XY.search(z)
        if not m:
            continue
        p = (float(m.group(1)), float(m.group(2)))
        if letzter is not None:
            laenge += math.hypot(p[0] - letzter[0], p[1] - letzter[1])
        letzter = p

    return ausgabe, striche, (xmin, xmax, ymin, ymax), laenge


def main():
    parser = argparse.ArgumentParser(
        description="Säubert svg2gcode-Ausgabe für den Walldraw-Polargraphen.")
    parser.add_argument("eingabe",
                        help="G-code-Datei von svg2gcode (z. B. schneemann.gcode)")
    parser.add_argument("ausgabe",
                        help="Zieldatei (z. B. 1.nc für die TF-Karte)")
    parser.add_argument("--zentrieren", action="store_true",
                        help="Zeichnung um die Home-Position (0|0) zentrieren")
    args = parser.parse_args()

    with open(args.eingabe, encoding="utf-8") as f:
        text = f.read()

    ausgabe, striche, (xmin, xmax, ymin, ymax), laenge = waschen(
        text, args.zentrieren)

    with open(args.ausgabe, "w", encoding="utf-8") as f:
        f.write("\n".join(ausgabe) + "\n")

    print("Fertig! Statistik:")
    print("  Zeilen        :", len(ausgabe))
    print("  Striche       :", striche)
    print("  Zeichnung     : %.0f x %.0f mm" % (xmax - xmin, ymax - ymin))
    print("  Weglänge      : %.1f m" % (laenge / 1000.0))
    print("  Zeit ca.      : %.0f min (bei 25 mm/s)" % (laenge / 25.0 / 60.0))


if __name__ == "__main__":
    main()
